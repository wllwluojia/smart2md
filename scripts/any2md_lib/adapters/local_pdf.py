from __future__ import annotations

from typing import Any

try:
    import fitz  # type: ignore
except ImportError:  # pragma: no cover
    fitz = None

from any2md_lib.models import AdapterResult, AdapterStatus, ExtractionContext
from any2md_lib.normalizers import normalize_text, now_iso


class LocalPdfAdapter:
    name = "local-pdf"

    def check(self, context: ExtractionContext) -> AdapterStatus:
        return AdapterStatus(
            name=self.name,
            available=fitz is not None,
            detail="PyMuPDF-backed local PDF extractor." if fitz is not None else "Install PyMuPDF to enable local PDF fallback.",
        )

    def supports(self, file_type: str) -> bool:
        return file_type == "pdf"

    def extract(self, context: ExtractionContext) -> AdapterResult:
        if fitz is None:
            raise RuntimeError("PyMuPDF is not installed.")
        pages: list[dict[str, Any]] = []
        doc = fitz.open(str(context.input_path))
        try:
            for page_number, page in enumerate(doc, start=1):
                width = float(page.rect.width)
                height = float(page.rect.height)
                raw = page.get_text("dict")
                blocks = []
                for block in raw.get("blocks", []):
                    if block.get("type") != 0:
                        continue
                    lines = []
                    for line in block.get("lines", []):
                        spans = [span.get("text", "") for span in line.get("spans", [])]
                        line_text = normalize_text("".join(spans))
                        if line_text:
                            lines.append(line_text)
                    text = "\n".join(lines)
                    if not text:
                        continue
                    x0, y0, x1, y1 = block["bbox"]
                    blocks.append(
                        {
                            "id": f"p{page_number}-b{len(blocks)+1}",
                            "kind": "text",
                            "role": "body",
                            "text": text,
                            "source_kind": "pdf-text",
                            "bbox": {
                                "x": round(x0 / width, 4),
                                "y": round(y0 / height, 4),
                                "w": round((x1 - x0) / width, 4),
                                "h": round((y1 - y0) / height, 4),
                            },
                            "reading_rank": len(blocks) + 1,
                        }
                    )
                title = blocks[0]["text"].splitlines()[0] if blocks else f"Page {page_number}"
                if blocks:
                    blocks[0]["role"] = "title"
                pages.append(
                    {
                        "page_number": page_number,
                        "title": title,
                        "layout_type": "text",
                        "width": width,
                        "height": height,
                        "summary": title,
                        "blocks": blocks,
                        "regions": [],
                        "flows": [],
                        "table": None,
                        "signals": {
                            "has_columns": False,
                            "has_timeline_keywords": False,
                            "has_architecture_keywords": False,
                            "has_process_keywords": False,
                        },
                    }
                )
        finally:
            doc.close()
        return AdapterResult(
            adapter_name=self.name,
            document={
                "source_path": str(context.input_path),
                "source_type": "pdf",
                "created_at": now_iso(),
                "adapter": self.name,
                "pages": pages,
            },
        )


ADAPTERS = [LocalPdfAdapter]
