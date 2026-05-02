from __future__ import annotations

import shutil
import subprocess

from pathlib import Path

from any2md_lib.config import adapter_settings
from any2md_lib.models import AdapterResult, AdapterStatus, ExtractionContext
from any2md_lib.normalizers import now_iso


class MineruAdapter:
    name = "mineru"

    def _command(self, context: ExtractionContext) -> str:
        return adapter_settings(context.config, self.name).get("command", "mineru")

    def check(self, context: ExtractionContext) -> AdapterStatus:
        command = self._command(context)
        resolved = shutil.which(command)
        return AdapterStatus(name=self.name, available=resolved is not None, detail=resolved or f"Command `{command}` not found.")

    def supports(self, file_type: str) -> bool:
        return file_type in {"pdf", "pptx", "xlsx"}

    def _cli_args(self, context: ExtractionContext, raw_dir: Path) -> list[str]:
        command = self._command(context)
        settings = adapter_settings(context.config, self.name)
        args = [command, "-p", str(context.input_path), "-o", str(raw_dir)]

        backend = settings.get("backend", "pipeline")
        if backend:
            args += ["-b", backend]

        method = settings.get("method", "")
        if method:
            args += ["-m", method]

        if settings.get("formula", True) is False:
            args += ["-f", "false"]
        if settings.get("table", True) is False:
            args += ["-t", "false"]

        return args

    def extract(self, context: ExtractionContext) -> AdapterResult:
        raw_root = context.raw_output_dir or context.output_dir
        raw_dir = raw_root / "mineru"
        raw_dir.mkdir(parents=True, exist_ok=True)
        timeout_seconds = int(adapter_settings(context.config, self.name).get("timeout_seconds", 120))
        cli_args = self._cli_args(context, raw_dir)
        subprocess.run(
            cli_args,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        document = {
            "source_path": str(context.input_path),
            "source_type": context.input_path.suffix.lower().lstrip("."),
            "created_at": now_iso(),
            "adapter": self.name,
            "pages": [],
            "warnings": ["MinerU raw output captured. Add a richer normalizer once the target CLI contract is fixed in your environment."],
        }
        return AdapterResult(
            adapter_name=self.name,
            document=document,
            raw_outputs={"mineru_raw_dir": str(raw_dir)},
        )


ADAPTERS = [MineruAdapter]
