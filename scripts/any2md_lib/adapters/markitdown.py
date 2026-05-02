from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from any2md_lib.config import adapter_settings
from any2md_lib.models import AdapterResult, AdapterStatus, ExtractionContext
from any2md_lib.normalizers import normalize_text, now_iso, sanitize_filename


class MarkItDownAdapter:
    name = "markitdown"

    def _command(self, context: ExtractionContext) -> str:
        settings = adapter_settings(context.config, self.name)
        return settings.get("command", "markitdown")

    def check(self, context: ExtractionContext) -> AdapterStatus:
        command = self._command(context)
        resolved = shutil.which(command)
        return AdapterStatus(
            name=self.name,
            available=resolved is not None,
            detail=resolved or f"Command `{command}` not found.",
        )

    def supports(self, file_type: str) -> bool:
        return True

    def extract(self, context: ExtractionContext) -> AdapterResult:
        command = self._command(context)
        result = subprocess.run([command, str(context.input_path)], check=True, capture_output=True, text=True)
        raw_root = context.raw_output_dir or context.output_dir
        baseline_dir = raw_root / "markitdown"
        baseline_dir.mkdir(parents=True, exist_ok=True)
        baseline_path = baseline_dir / f"{sanitize_filename(context.input_path.stem)}.baseline.md"
        baseline_path.write_text(result.stdout, encoding="utf-8")
        content = normalize_text(result.stdout)
        document = {
            "source_path": str(context.input_path),
            "source_type": context.input_path.suffix.lower().lstrip("."),
            "created_at": now_iso(),
            "adapter": self.name,
            "pages": [
                {
                    "page_number": 1,
                    "title": context.input_path.stem,
                    "layout_type": "baseline",
                    "summary": content.splitlines()[0] if content else context.input_path.stem,
                    "blocks": [
                        {
                            "id": "p1-b1",
                            "kind": "text",
                            "role": "body",
                            "text": content,
                            "source_kind": "markitdown",
                            "bbox": {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0},
                            "reading_rank": 1,
                        }
                    ],
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
            ],
            "final_markdown_path": str(baseline_path),
        }
        return AdapterResult(
            adapter_name=self.name,
            document=document,
            raw_outputs={"baseline_markdown": str(baseline_path)},
        )


ADAPTERS = [MarkItDownAdapter]
