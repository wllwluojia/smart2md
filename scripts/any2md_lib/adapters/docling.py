from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from any2md_lib.config import adapter_settings
from any2md_lib.models import AdapterResult, AdapterStatus, ExtractionContext
from any2md_lib.normalizers import now_iso


class DoclingAdapter:
    name = "docling"

    def _command(self, context: ExtractionContext) -> str:
        return adapter_settings(context.config, self.name).get("command", "docling")

    def check(self, context: ExtractionContext) -> AdapterStatus:
        command = self._command(context)
        resolved = shutil.which(command)
        return AdapterStatus(name=self.name, available=resolved is not None, detail=resolved or f"Command `{command}` not found.")

    def supports(self, file_type: str) -> bool:
        return file_type in {"pdf", "docx"}

    def _find_primary_output(self, output_dir: Path, suffix: str) -> Path | None:
        candidates = sorted(output_dir.glob(f"*.{suffix}"))
        return candidates[0] if candidates else None

    def extract(self, context: ExtractionContext) -> AdapterResult:
        command = self._command(context)
        settings = adapter_settings(context.config, self.name)
        raw_root = context.raw_output_dir or context.output_dir
        output_dir = raw_root / "docling"
        output_dir.mkdir(parents=True, exist_ok=True)
        fmt = context.input_path.suffix.lower().lstrip(".")
        timeout_seconds = int(settings.get("timeout_seconds", 120))
        image_export_mode = settings.get("image_export_mode", "placeholder")
        subprocess.run(
            [
                command,
                str(context.input_path),
                "--from",
                fmt,
                "--to",
                "md",
                "--to",
                "json",
                "--output",
                str(output_dir),
                "--image-export-mode",
                str(image_export_mode),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        markdown_path = self._find_primary_output(output_dir, "md")
        json_path = self._find_primary_output(output_dir, "json")
        document = {
            "source_path": str(context.input_path),
            "source_type": context.input_path.suffix.lower().lstrip("."),
            "created_at": now_iso(),
            "adapter": self.name,
            "pages": [],
        }
        if markdown_path:
            document["final_markdown_path"] = str(markdown_path)
        else:
            document["warnings"] = ["Docling finished but no Markdown output file was found."]
        return AdapterResult(
            adapter_name=self.name,
            document=document,
            raw_outputs={
                "docling_raw_dir": str(output_dir),
                **({"docling_markdown": str(markdown_path)} if markdown_path else {}),
                **({"docling_json": str(json_path)} if json_path else {}),
            },
        )


ADAPTERS = [DoclingAdapter]
