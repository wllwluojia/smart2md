from __future__ import annotations

import importlib
import pkgutil
import re

try:
    import fitz  # type: ignore
except ImportError:  # pragma: no cover
    fitz = None

from any2md_lib.config import route_chain
from any2md_lib.models import AdapterStatus, ExtractionContext, RouteDecision
from any2md_lib.adapters.base import detect_file_type
from any2md_lib import adapters as adapters_pkg


def build_registry():
    registry = {}
    prefix = adapters_pkg.__name__ + "."
    for _, module_name, _ in pkgutil.iter_modules(adapters_pkg.__path__, prefix):
        if module_name.endswith(".base"):
            continue
        module = importlib.import_module(module_name)
        for adapter_cls in getattr(module, "ADAPTERS", []):
            adapter = adapter_cls()
            registry[adapter.name] = adapter
    return registry


def _pdf_profile_chain(context: ExtractionContext, profile: str, fallback: list[str]) -> list[str]:
    routing = context.config.get("routing", {})
    if profile == "fast":
        return list(routing.get("pdf_fast") or fallback)
    if profile == "standard":
        return list(routing.get("pdf_standard") or fallback)
    if profile == "complex":
        return list(routing.get("pdf_complex") or fallback)
    return fallback


def _collect_pdf_signals(context: ExtractionContext) -> dict[str, float | int]:
    if fitz is None:
        return {}
    settings = context.config.get("routing", {}).get("pymupdf_router", {})
    sample_pages = int(settings.get("sample_pages", 5))
    inspected_pages = 0
    text_chars = 0
    text_blocks = 0
    image_blocks = 0
    heading_count = 0
    table_hits = 0
    doc = fitz.open(str(context.input_path))
    try:
        for page in doc:
            inspected_pages += 1
            raw = page.get_text("dict")
            for block in raw.get("blocks", []):
                block_type = block.get("type")
                if block_type == 1:
                    image_blocks += 1
                    continue
                if block_type != 0:
                    continue
                block_text_parts = []
                max_font = 0.0
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "")
                        if text:
                            block_text_parts.append(text)
                        max_font = max(max_font, float(span.get("size", 0.0)))
                block_text = "".join(block_text_parts).strip()
                if not block_text:
                    continue
                text_blocks += 1
                text_chars += len(block_text)
                if max_font >= 14 and len(block_text) <= 80:
                    heading_count += 1
                if re.search(r"(\|.+\|)|(\t)|([A-Za-z0-9\u4e00-\u9fff]+\s{2,}[A-Za-z0-9\u4e00-\u9fff]+)", block_text):
                    table_hits += 1
            if inspected_pages >= sample_pages:
                break
    finally:
        doc.close()
    if inspected_pages == 0:
        return {}
    return {
        "inspected_pages": inspected_pages,
        "avg_text_chars_per_page": text_chars / inspected_pages,
        "avg_text_blocks_per_page": text_blocks / inspected_pages,
        "image_blocks_total": image_blocks,
        "heading_count": heading_count,
        "table_hits": table_hits,
    }


def _resolve_pdf_chain(context: ExtractionContext, chain: list[str]) -> list[str]:
    if not chain or chain[0] != "pymupdf-router":
        return chain
    fallback = [item for item in chain if item != "pymupdf-router"]
    settings = context.config.get("routing", {}).get("pymupdf_router", {})
    signals = _collect_pdf_signals(context)
    if not signals:
        return _pdf_profile_chain(context, "standard", fallback)

    avg_text_chars = float(signals["avg_text_chars_per_page"])
    avg_text_blocks = float(signals["avg_text_blocks_per_page"])
    image_blocks = int(signals["image_blocks_total"])
    heading_count = int(signals["heading_count"])
    table_hits = int(signals["table_hits"])

    if (
        avg_text_chars <= float(settings.get("complex_low_text_chars_per_page", 120))
        or image_blocks >= int(settings.get("complex_image_blocks_total", 2))
        or avg_text_blocks >= float(settings.get("complex_text_blocks_per_page", 28))
        or table_hits >= int(settings.get("complex_table_hits", 2))
    ):
        return _pdf_profile_chain(context, "complex", fallback)

    if (
        avg_text_chars >= float(settings.get("simple_text_chars_per_page", 1200))
        and avg_text_blocks <= float(settings.get("simple_max_text_blocks_per_page", 24))
        and image_blocks <= int(settings.get("simple_max_image_blocks_total", 0))
        and heading_count < int(settings.get("heading_min_count", 3))
    ):
        return _pdf_profile_chain(context, "fast", fallback)

    return _pdf_profile_chain(context, "standard", fallback)


def decide_route(context: ExtractionContext, backend_override: str | None = None) -> RouteDecision:
    file_type = detect_file_type(context.input_path)
    if backend_override:
        return RouteDecision(file_type=file_type, backend_chain=[backend_override])
    chain = route_chain(context.config, file_type)
    if file_type == "pdf":
        chain = _resolve_pdf_chain(context, chain)
    return RouteDecision(file_type=file_type, backend_chain=chain)


def doctor(context: ExtractionContext) -> list[AdapterStatus]:
    registry = build_registry()
    return [adapter.check(context) for adapter in registry.values()]
