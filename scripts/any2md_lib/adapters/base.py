from __future__ import annotations

from pathlib import Path
from typing import Protocol

from any2md_lib.models import AdapterResult, AdapterStatus, ExtractionContext


class Adapter(Protocol):
    name: str

    def check(self, context: ExtractionContext) -> AdapterStatus: ...

    def supports(self, file_type: str) -> bool: ...

    def extract(self, context: ExtractionContext) -> AdapterResult: ...


def detect_file_type(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    return suffix or "unknown"
