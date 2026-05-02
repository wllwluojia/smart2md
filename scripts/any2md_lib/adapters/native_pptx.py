from __future__ import annotations

import dataclasses
import re
import zipfile
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as ET

from any2md_lib.models import AdapterResult, AdapterStatus, ExtractionContext
from any2md_lib.normalizers import normalize_text, now_iso

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}

TITLE_HINTS = ("title", "现状", "规划", "方案", "架构", "流程", "系统", "计划", "路径", "思路", "目标")
ARCHITECTURE_HINTS = ("架构", "平台", "中心", "层", "能力", "数据中台", "标签", "策略", "产品中心", "任务中心", "crm")
PROCESS_HINTS = ("流程", "下发", "流转", "触达", "客户洞察", "营销策略", "任务", "审批", "回流", "执行")
TIMELINE_HINTS = ("阶段", "里程碑", "计划", "t+", "月", "季度", "投产", "准备", "实施")
CARD_HINTS = ("中心", "平台", "体系", "机制", "策略", "管理", "团队", "实力", "资质", "风险", "建议", "方案")


@dataclasses.dataclass
class BBox:
    x: float
    y: float
    w: float
    h: float

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    def to_dict(self) -> dict[str, float]:
        return {"x": round(self.x, 4), "y": round(self.y, 4), "w": round(self.w, 4), "h": round(self.h, 4)}


@dataclasses.dataclass
class Block:
    id: str
    text: str
    bbox: BBox
    kind: str = "text"
    role: str = "body"
    source_kind: str = "native"
    reading_rank: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "role": self.role,
            "text": self.text,
            "source_kind": self.source_kind,
            "bbox": self.bbox.to_dict(),
            "reading_rank": self.reading_rank,
        }


def sanitize_label(text: str) -> str:
    first = normalize_text(text).splitlines()[0] if text else ""
    first = re.sub(r"[^\w\u4e00-\u9fff]+", " ", first).strip()
    return first[:30] if first else "region"


def cluster_positions(values: list[float], tolerance: float) -> list[list[int]]:
    if not values:
        return []
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    clusters: list[list[int]] = [[indexed[0][0]]]
    prev = indexed[0][1]
    for idx, value in indexed[1:]:
        if abs(value - prev) <= tolerance:
            clusters[-1].append(idx)
        else:
            clusters.append([idx])
        prev = value
    return clusters


def merge_bboxes(boxes: Iterable[BBox]) -> BBox:
    boxes = list(boxes)
    return BBox(
        x=min(box.x for box in boxes),
        y=min(box.y for box in boxes),
        w=max(box.right for box in boxes) - min(box.x for box in boxes),
        h=max(box.bottom for box in boxes) - min(box.y for box in boxes),
    )


def parse_runs(node: ET.Element) -> str:
    pieces: list[str] = []
    for paragraph in node.findall(".//a:p", NS):
        runs = [normalize_text(t.text or "") for t in paragraph.findall(".//a:t", NS)]
        line = "".join(part for part in runs if part)
        if line:
            pieces.append(line)
    return "\n".join(pieces)


def meaningful(text: str, bbox: BBox) -> bool:
    lowered = normalize_text(text).lower()
    if not lowered:
        return False
    if lowered.startswith("picture") and bbox.w >= 0.9 and bbox.h >= 0.9:
        return False
    if re.fullmatch(r"(image|图片|图片 \d+|图像|picture)\s*", lowered):
        return False
    if bbox.w <= 0 or bbox.h <= 0:
        return False
    return True


def title_score(block: Block) -> tuple[float, float, float]:
    lowered = block.text.lower()
    hint_bonus = 1.0 if any(h in lowered for h in TITLE_HINTS) else 0.0
    role_bonus = 1.5 if block.role == "title" else (0.4 if block.role == "body" else 0.0)
    return (-block.bbox.y, block.bbox.h + hint_bonus + role_bonus, block.bbox.w)


def assign_ranks(blocks: list[Block]) -> None:
    ordered = sorted(blocks, key=lambda b: (round(b.bbox.y / 0.03), b.bbox.x, -b.bbox.h))
    for rank, block in enumerate(ordered, start=1):
        block.reading_rank = rank


def detect_layout(title: str, blocks: list[Block], regions: list[dict[str, Any]], has_table: bool) -> tuple[str, dict[str, bool]]:
    text_blob = " ".join(block.text.lower() for block in blocks if meaningful(block.text, block.bbox))
    title_lower = title.lower()
    signals = {
        "has_columns": len(regions) >= 3,
        "has_timeline_keywords": any(word in text_blob for word in TIMELINE_HINTS),
        "has_architecture_keywords": any(word in text_blob or word in title_lower for word in ARCHITECTURE_HINTS),
        "has_process_keywords": any(word in text_blob or word in title_lower for word in PROCESS_HINTS),
    }
    if has_table:
        return "table", signals
    if len([block for block in blocks if meaningful(block.text, block.bbox)]) <= 4:
        return "cover", signals
    if signals["has_timeline_keywords"]:
        return "timeline", signals
    if signals["has_process_keywords"] and len(regions) >= 3:
        return "process", signals
    if signals["has_architecture_keywords"] and len(regions) >= 2:
        return "architecture", signals
    if len(regions) >= 3:
        return "cards", signals
    return "text", signals


def shape_bbox(node: ET.Element, slide_width: int, slide_height: int) -> BBox | None:
    xfrm = node.find(".//a:xfrm", NS) or node.find(".//p:xfrm", NS)
    if xfrm is None:
        return None
    off = xfrm.find("./a:off", NS)
    ext = xfrm.find("./a:ext", NS)
    if off is None or ext is None:
        return None
    return BBox(
        x=int(off.attrib.get("x", "0")) / slide_width,
        y=int(off.attrib.get("y", "0")) / slide_height,
        w=int(ext.attrib.get("cx", "0")) / slide_width,
        h=int(ext.attrib.get("cy", "0")) / slide_height,
    )


def is_title_placeholder(node: ET.Element) -> bool:
    ph = node.find(".//p:nvPr/p:ph", NS)
    return ph is not None and ph.attrib.get("type", "") in {"title", "ctrTitle", "subTitle"}


def build_regions(page_prefix: str, blocks: list[Block]) -> list[dict[str, Any]]:
    body_blocks = [block for block in blocks if block.role not in {"title", "subtitle"} and meaningful(block.text, block.bbox)]
    if len(body_blocks) < 3:
        return []
    heading_candidates = [block for block in body_blocks if _is_heading_like(block) and 0.18 <= block.bbox.y <= 0.75]
    heading_rows = cluster_positions([block.bbox.y for block in heading_candidates], tolerance=0.08)
    if heading_rows:
        best_row = max(
            heading_rows,
            key=lambda row: (len(row), -min(heading_candidates[i].bbox.y for i in row)),
        )
        anchors = [heading_candidates[i] for i in best_row]
        if len(anchors) >= 2:
            anchors = sorted(anchors, key=lambda block: block.bbox.cx)
            centers = [anchor.bbox.cx for anchor in anchors]
            spans: list[tuple[float, float]] = []
            for idx, center in enumerate(centers):
                left = 0.0 if idx == 0 else (centers[idx - 1] + center) / 2
                right = 1.0 if idx == len(centers) - 1 else (center + centers[idx + 1]) / 2
                spans.append((left, right))
            regions = []
            for idx, (anchor, span) in enumerate(zip(anchors, spans), start=1):
                members = []
                for block in body_blocks:
                    if block.bbox.w > 0.6 and block.bbox.y > 0.75:
                        continue
                    if block.bbox.cx < span[0] or block.bbox.cx >= span[1]:
                        continue
                    if block.bbox.y + block.bbox.h < anchor.bbox.y - 0.03:
                        continue
                    members.append(block)
                if not members:
                    members = [anchor]
                members = sorted(members, key=lambda block: (block.bbox.y, block.bbox.x))
                bbox = merge_bboxes(member.bbox for member in members)
                regions.append(
                    {
                        "id": f"{page_prefix}-r{idx}",
                        "label": f"column-{idx}",
                        "bbox": bbox.to_dict(),
                        "block_ids": [member.id for member in members],
                        "previews": [member.text.splitlines()[0] for member in members[:6]],
                    }
                )
            return regions
    clusters = cluster_positions([block.bbox.cx for block in body_blocks], tolerance=0.12)
    if len(clusters) <= 1:
        return []
    regions = []
    for idx, cluster in enumerate(sorted(clusters, key=lambda c: min(body_blocks[i].bbox.x for i in c)), start=1):
        members = [body_blocks[i] for i in cluster]
        if len(members) == 1 and members[0].bbox.w > 0.7:
            continue
        bbox = merge_bboxes(member.bbox for member in members)
        regions.append(
            {
                "id": f"{page_prefix}-r{idx}",
                "label": f"column-{idx}",
                "bbox": bbox.to_dict(),
                "block_ids": [member.id for member in sorted(members, key=lambda b: (b.bbox.y, b.bbox.x))],
                "previews": [member.text.splitlines()[0] for member in members[:6]],
            }
        )
    return regions


def build_flows(regions: list[dict[str, Any]], block_lookup: dict[str, Block], layout_type: str) -> list[dict[str, str]]:
    if layout_type not in {"process", "timeline", "architecture"} or len(regions) < 2:
        return []
    labels = []
    for region in regions:
        preview = next(
            (
                block_lookup[block_id].text
                for block_id in region["block_ids"]
                if block_id in block_lookup and meaningful(block_lookup[block_id].text, block_lookup[block_id].bbox)
            ),
            region["label"],
        )
        labels.append(sanitize_label(preview))
    return [
        {"from": src, "to": dst, "evidence": "left-to-right region sequence"}
        for src, dst in zip(labels, labels[1:])
        if src != dst
    ]


def _block_text(block: Block) -> str:
    return normalize_text(block.text).replace("\n", " / ").strip()


def _is_heading_like(block: Block) -> bool:
    text = _block_text(block)
    if not text or len(text) > 42:
        return False
    if any(mark in text for mark in ("：", ":", "。", "；")) and len(text) > 22:
        return False
    if block.bbox.h >= 0.11:
        return False
    return len(text) <= 18 or any(hint in text for hint in CARD_HINTS)


def build_sections(page_title: str, regions: list[dict[str, Any]], block_lookup: dict[str, Block], layout_type: str) -> list[dict[str, Any]]:
    if layout_type not in {"cards", "timeline", "process", "architecture"} or not regions:
        return []
    sections: list[dict[str, Any]] = []
    for idx, region in enumerate(regions, start=1):
        members = [
            block_lookup[block_id]
            for block_id in region.get("block_ids", [])
            if block_id in block_lookup and meaningful(block_lookup[block_id].text, block_lookup[block_id].bbox)
        ]
        members = [member for member in members if member.role != "image-placeholder"]
        if not members:
            continue
        members = sorted(members, key=lambda block: (block.bbox.y, block.bbox.x))
        heading = next((member for member in members if _is_heading_like(member)), members[0])
        body_blocks = [member for member in members if member.id != heading.id]
        body = [_block_text(member) for member in body_blocks if _block_text(member)]
        summary = body[0] if body else _block_text(heading)
        sections.append(
            {
                "id": region["id"],
                "title": _block_text(heading),
                "summary": summary,
                "points": body[:6],
                "block_ids": [member.id for member in members],
            }
        )
    seen_titles: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for section in sections:
        title = section["title"]
        if not title or title == page_title or title in seen_titles:
            continue
        seen_titles.add(title)
        deduped.append(section)
    return deduped


class NativePptxAdapter:
    name = "native-pptx"

    def check(self, context: ExtractionContext) -> AdapterStatus:
        return AdapterStatus(name=self.name, available=True, detail="Built-in Office XML parser.")

    def supports(self, file_type: str) -> bool:
        return file_type == "pptx"

    def extract(self, context: ExtractionContext) -> AdapterResult:
        pages: list[dict[str, Any]] = []
        with zipfile.ZipFile(context.input_path) as archive:
            presentation_xml = ET.fromstring(archive.read("ppt/presentation.xml"))
            sld_sz = presentation_xml.find("./p:sldSz", NS)
            slide_width = int(sld_sz.attrib["cx"]) if sld_sz is not None else 9144000
            slide_height = int(sld_sz.attrib["cy"]) if sld_sz is not None else 5143500
            slide_names = sorted(name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name))
            for page_number, slide_name in enumerate(slide_names, start=1):
                pages.append(self._parse_slide(archive.read(slide_name), slide_width, slide_height, page_number))
        document = {
            "source_path": str(context.input_path),
            "source_type": "pptx",
            "created_at": now_iso(),
            "adapter": self.name,
            "pages": pages,
        }
        return AdapterResult(adapter_name=self.name, document=document)

    def _parse_slide(self, slide_xml: bytes, slide_width: int, slide_height: int, page_number: int) -> dict[str, Any]:
        root = ET.fromstring(slide_xml)
        blocks: list[Block] = []
        table_rows: list[list[str]] = []
        has_table = False
        page_prefix = f"p{page_number}"

        def visit(node: ET.Element) -> None:
            nonlocal has_table
            local_name = node.tag.split("}")[-1]
            if local_name == "grpSp":
                for child in node:
                    child_name = child.tag.split("}")[-1]
                    if child_name in {"sp", "grpSp", "graphicFrame", "pic"}:
                        visit(child)
                return
            if local_name == "sp":
                text = parse_runs(node)
                bbox = shape_bbox(node, slide_width, slide_height)
                if text and bbox and meaningful(text, bbox):
                    blocks.append(
                        Block(
                            id=f"{page_prefix}-b{len(blocks)+1}",
                            text=text,
                            bbox=bbox,
                            role="title" if is_title_placeholder(node) else "body",
                        )
                    )
            elif local_name == "graphicFrame":
                bbox = shape_bbox(node, slide_width, slide_height)
                tbl = node.find(".//a:tbl", NS)
                if tbl is not None and bbox is not None:
                    has_table = True
                    table_text = []
                    for row in tbl.findall("./a:tr", NS):
                        cells = [parse_runs(cell) for cell in row.findall("./a:tc", NS)]
                        if any(cells):
                            table_rows.append(cells)
                            table_text.append(" | ".join(cells))
                    if table_text:
                        blocks.append(
                            Block(
                                id=f"{page_prefix}-b{len(blocks)+1}",
                                text="\n".join(table_text),
                                bbox=bbox,
                                role="table",
                                source_kind="table",
                            )
                        )
            elif local_name == "pic":
                bbox = shape_bbox(node, slide_width, slide_height)
                if bbox is not None and bbox.w > 0 and bbox.h > 0:
                    c_nv_pr = node.find(".//p:cNvPr", NS)
                    label = normalize_text(c_nv_pr.attrib.get("name", "") if c_nv_pr is not None else "") or "image"
                    blocks.append(
                        Block(
                            id=f"{page_prefix}-b{len(blocks)+1}",
                            text=label,
                            bbox=bbox,
                            kind="image",
                            role="image-placeholder",
                        )
                    )

        sp_tree = root.find(".//p:spTree", NS)
        if sp_tree is not None:
            for child in sp_tree:
                if child.tag.split("}")[-1] in {"sp", "grpSp", "graphicFrame", "pic"}:
                    visit(child)

        blocks = [block for block in blocks if meaningful(block.text, block.bbox) or block.role == "image-placeholder"]

        if not blocks:
            blocks = [Block(id=f"{page_prefix}-b1", text="(empty slide)", bbox=BBox(0.1, 0.1, 0.8, 0.1))]

        assign_ranks(blocks)
        title_candidates = [block for block in blocks if block.role == "title" and meaningful(block.text, block.bbox)]
        if not title_candidates:
            title_candidates = [block for block in blocks if meaningful(block.text, block.bbox)] or blocks
        title = sorted(title_candidates, key=title_score, reverse=True)[0].text.splitlines()[0]
        for block in blocks:
            if block.role != "title" and meaningful(block.text, block.bbox) and block.bbox.y < 0.2 and len(block.text) < 80:
                block.role = "subtitle"
        regions = build_regions(page_prefix, blocks)
        block_lookup = {block.id: block for block in blocks}
        layout_type, signals = detect_layout(title, blocks, regions, has_table)
        flows = build_flows(regions, block_lookup, layout_type)
        sections = build_sections(title, regions, block_lookup, layout_type)
        summary_parts = [title] + [section["title"] for section in sections[:3]]
        summary = "；".join(summary_parts[:4])
        return {
            "page_number": page_number,
            "title": title,
            "layout_type": layout_type,
            "width": slide_width,
            "height": slide_height,
            "summary": summary,
            "blocks": [block.to_dict() for block in sorted(blocks, key=lambda item: item.reading_rank)],
            "regions": regions,
            "sections": sections,
            "flows": flows,
            "table": table_rows or None,
            "signals": signals,
        }


ADAPTERS = [NativePptxAdapter]
