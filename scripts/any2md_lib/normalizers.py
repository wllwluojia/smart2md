from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
import shutil
from typing import Any


def now_iso() -> str:
    tz = dt.timezone(dt.timedelta(hours=8))
    return dt.datetime.now(tz).isoformat(timespec="seconds")


def sanitize_filename(text: str) -> str:
    cleaned = re.sub(r"[^\w\-.]+", "-", text, flags=re.UNICODE).strip("-")
    return cleaned or "output"


def normalize_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def render_markdown(doc: dict[str, Any], baseline_path: Path | None) -> str:
    source_name = Path(str(doc['source_path'])).name
    lines = [
        "---",
        f"source_path: {json.dumps(str(doc.get('source_path', '')))}",
        f"source_type: {json.dumps(str(doc.get('source_type', '')))}",
        f"created_at: {json.dumps(str(doc.get('created_at', '')))}",
        f"baseline_markdown_path: {json.dumps(str(baseline_path) if baseline_path else '')}",
        f"adapter: {json.dumps(str(doc.get('adapter', '')))}",
        f"tags: [any2md, structured, {json.dumps(str(doc.get('source_type', '')))}]",
        f"aliases: [{json.dumps(source_name)}]",
        "---",
        "",
        f"# Structured Extract: {source_name}",
        "",
    ]
    if doc.get("warnings"):
        lines.append("> [!warning] Warnings")
        for warning in doc["warnings"]:
            lines.append(f"> - {warning}")
        lines.append("")
    if not doc.get("pages"):
        lines.extend(["No structured pages were extracted.", ""])
    for page in doc.get("pages", []):
        lines.extend(
            [
                f"## Page {page['page_number']}: {page['title']}",
                "",
                f"- Layout: `{page.get('layout_type', 'unknown')}`",
            ]
        )
        summary = page.get('summary', '')
        if summary:
            lines.append("> [!abstract] Summary")
            lines.append(f"> {summary}")
            lines.append("")
        
        regions = page.get("regions") or []
        if regions:
            lines.append("### Regions")
            for region in regions:
                lines.append(f"- `{region['label']}`")
                for preview in region.get("previews", [])[:6]:
                    lines.append(f"  - {preview}")
            lines.append("")
        sections = page.get("sections") or []
        if sections:
            lines.append("### Sections")
            for section in sections:
                lines.append(f"- **{section['title']}**")
                if section.get("summary"):
                    lines.append(f"  - {section['summary']}")
                for point in section.get("points", [])[:4]:
                    if point != section.get("summary"):
                        lines.append(f"  - {point}")
            lines.append("")
        flows = page.get("flows") or []
        if flows:
            lines.append("### Flow")
            for edge in flows:
                lines.append(f"- {edge['from']} -> {edge['to']} ({edge['evidence']})")
            lines.append("")
        table = page.get("table")
        if table:
            lines.append("### Table")
            header = table[0]
            lines.append("| " + " | ".join(header) + " |")
            lines.append("| " + " | ".join("---" for _ in header) + " |")
            for row in table[1:]:
                padded = row + [""] * (len(header) - len(row))
                lines.append("| " + " | ".join(padded[: len(header)]) + " |")
            lines.append("")
        if page.get("blocks"):
            lines.append("### Blocks")
            for block in page["blocks"]:
                bbox = block.get("bbox", {})
                preview = str(block.get("text", "")).replace("\n", " / ")
                lines.append(
                    f"- `{block.get('role', 'body')}` @ ({bbox.get('x', 0):.2f}, {bbox.get('y', 0):.2f}, {bbox.get('w', 0):.2f}, {bbox.get('h', 0):.2f}): {preview}"
                )
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _clean_block_text(text: str) -> str:
    text = normalize_text(text)
    text = text.replace("◼", "").replace("•", "").strip()
    text = re.sub(r"\s*/\s*", " / ", text)
    return text


def _is_noise_text(text: str) -> bool:
    lowered = text.strip().lower()
    if not lowered:
        return True
    if re.fullmatch(r"\d+", lowered):
        return True
    if lowered in {"image", "contents"}:
        return True
    return False


def _select_readable_points(page: dict[str, Any], limit: int = 12) -> list[str]:
    seen: set[str] = set()
    points: list[str] = []
    for block in page.get("blocks", []):
        role = block.get("role", "body")
        if role == "image-placeholder":
            continue
        text = _clean_block_text(str(block.get("text", "")))
        if _is_noise_text(text):
            continue
        if len(text) < 4 and role != "title":
            continue
        if text in seen:
            continue
        seen.add(text)
        points.append(text)
        if len(points) >= limit:
            break
    return points


def _split_point(text: str) -> list[str]:
    text = _clean_block_text(text)
    if not text:
        return []
    if " / " in text:
        return [part.strip() for part in text.split(" / ") if part.strip()]
    return [text]


def render_readable_markdown(doc: dict[str, Any]) -> str:
    source_name = Path(str(doc["source_path"])).name
    lines = [
        "---",
        f"source_path: {json.dumps(str(doc.get('source_path', '')))}",
        f"source_type: {json.dumps(str(doc.get('source_type', '')))}",
        f"created_at: {json.dumps(str(doc.get('created_at', '')))}",
        f"adapter: {json.dumps(str(doc.get('adapter', '')))}",
        'view: "readable"',
        f"tags: [any2md, extracted, {json.dumps(str(doc.get('source_type', '')))}]",
        f"aliases: [{json.dumps(source_name)}]",
        "---",
        "",
        f"# {source_name}",
        "",
        "## 阅读说明",
        "",
        "- 这是面向人工阅读和 Wiki 提炼的精简版。",
        "- 已去掉坐标、bbox、原始调试信息。",
        "- 更完整的机器可追溯信息保留在 `.structured.json` 中。",
        "",
    ]
    if doc.get("warnings"):
        lines.append("> [!warning] 注意")
        for warning in doc["warnings"]:
            lines.append(f"> - {warning}")
        lines.append("")
    for page in doc.get("pages", []):
        raw_title = str(page.get("title", "")).strip()
        title = raw_title if not _is_noise_text(raw_title) else f"第 {page['page_number']} 页"
        lines.append(f"## 第 {page['page_number']} 页：{title}")
        lines.append("")
        layout = page.get("layout_type", "unknown")
        
        summary = _clean_block_text(str(page.get("summary", "")))
        if summary and not _is_noise_text(summary) and summary != raw_title:
            lines.append("> [!abstract] 页面摘要")
            lines.append(f"> {summary}")
            lines.append("")
            
        if layout and layout != "unknown":
            lines.append(f"- 页面类型：`{layout}`")
        flows = page.get("flows") or []
        if flows:
            flow_text = "；".join(f"{edge['from']} -> {edge['to']}" for edge in flows[:8])
            lines.append(f"- 主要流程：{flow_text}")
        lines.append("")

        table = page.get("table")
        if table:
            lines.append("### 表格")
            lines.append("")
            header = table[0]
            lines.append("| " + " | ".join(header) + " |")
            lines.append("| " + " | ".join("---" for _ in header) + " |")
            for row in table[1:]:
                padded = row + [""] * (len(header) - len(row))
                lines.append("| " + " | ".join(_clean_block_text(cell) for cell in padded[: len(header)]) + " |")
            lines.append("")

        sections = page.get("sections") or []
        if sections:
            lines.append("### 关键信息")
            lines.append("")
            for section in sections:
                title_text = _clean_block_text(str(section.get("title", "")))
                if not title_text or _is_noise_text(title_text):
                    continue
                lines.append(f"#### {title_text}")
                lines.append("")
                summary_text = _clean_block_text(str(section.get("summary", "")))
                if summary_text and summary_text != title_text and not _is_noise_text(summary_text):
                    lines.append(f"- {summary_text}")
                seen: set[str] = set()
                if summary_text:
                    seen.add(summary_text)
                for point in section.get("points", [])[:6]:
                    for item in _split_point(point):
                        if item == title_text or item in seen or _is_noise_text(item):
                            continue
                        seen.add(item)
                        lines.append(f"- {item}")
                lines.append("")
            continue

        points = _select_readable_points(page)
        if points:
            lines.append("### 关键信息")
            lines.append("")
            for point in points:
                lines.append(f"- {point}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_mermaid(doc: dict[str, Any]) -> str:
    sections = [f"# Mermaid Views: {Path(str(doc['source_path'])).name}", ""]
    for page in doc.get("pages", []):
        flows = page.get("flows") or []
        if not flows:
            continue
        sections.append(f"## Page {page['page_number']}: {page['title']}")
        sections.append("")
        direction = "LR" if page.get("layout_type") != "timeline" else "TB"
        sections.append("```mermaid")
        sections.append(f"flowchart {direction}")
        emitted = set()
        for edge in flows:
            src = sanitize_filename(edge["from"])
            dst = sanitize_filename(edge["to"])
            if src not in emitted:
                sections.append(f'    {src}["{edge["from"]}"]')
                emitted.add(src)
            if dst not in emitted:
                sections.append(f'    {dst}["{edge["to"]}"]')
                emitted.add(dst)
            sections.append(f"    {src} --> {dst}")
        sections.append("```")
        sections.append("")
    return "\n".join(sections).rstrip() + "\n"


def write_outputs(doc: dict[str, Any], output_dir: Path, baseline_path: Path | None, write_debug_outputs: bool = False) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_path = Path(str(doc["source_path"]))
    stem = sanitize_filename(source_path.stem)
    json_path = output_dir / f"{stem}.structured.json"
    md_path = output_dir / f"{stem}.structured.md"
    mermaid_path = output_dir / f"{stem}.mermaid.md"
    readable_path = output_dir / f"{source_path.name}.md"
    if baseline_path:
        doc["baseline_markdown_path"] = str(baseline_path)
    final_markdown_path = doc.get("final_markdown_path")
    if final_markdown_path and Path(str(final_markdown_path)).exists():
        shutil.copyfile(Path(str(final_markdown_path)), readable_path)
    else:
        readable_path.write_text(render_readable_markdown(doc), encoding="utf-8")
    outputs: dict[str, Path] = {"readable": readable_path}
    if write_debug_outputs:
        json_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        md_path.write_text(render_markdown(doc, baseline_path), encoding="utf-8")
        mermaid_path.write_text(render_mermaid(doc), encoding="utf-8")
        outputs.update({"json": json_path, "markdown": md_path, "mermaid": mermaid_path})
    return outputs
