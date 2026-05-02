from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path

from any2md_lib.config import adapter_settings
from any2md_lib.models import AdapterResult, AdapterStatus, ExtractionContext
from any2md_lib.normalizers import now_iso


class PyMuPDF4LLMAdapter:
    name = "pymupdf4llm"

    def check(self, context: ExtractionContext) -> AdapterStatus:
        module_name = adapter_settings(context.config, self.name).get("module", "pymupdf4llm")
        available = importlib.util.find_spec(module_name) is not None
        detail = f"Python module `{module_name}` available." if available else f"Python module `{module_name}` not installed."
        return AdapterStatus(name=self.name, available=available, detail=detail)

    def supports(self, file_type: str) -> bool:
        return file_type == "pdf"

    def extract(self, context: ExtractionContext) -> AdapterResult:
        module_name = adapter_settings(context.config, self.name).get("module", "pymupdf4llm")
        pymupdf4llm = importlib.import_module(module_name)
        markdown = pymupdf4llm.to_markdown(str(context.input_path))
        raw_root = context.raw_output_dir or context.output_dir
        output_dir = raw_root / "pymupdf4llm"
        output_dir.mkdir(parents=True, exist_ok=True)
        markdown_path = output_dir / f"{Path(context.input_path).stem}.md"
        markdown_path.write_text(markdown, encoding="utf-8")
        document = {
            "source_path": str(context.input_path),
            "source_type": context.input_path.suffix.lower().lstrip("."),
            "created_at": now_iso(),
            "adapter": self.name,
            "pages": [],
            "final_markdown_path": str(markdown_path),
        }
        return AdapterResult(
            adapter_name=self.name,
            document=document,
            raw_outputs={"pymupdf4llm_markdown": str(markdown_path)},
        )


ADAPTERS = [PyMuPDF4LLMAdapter]
