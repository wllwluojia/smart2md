from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ExtractionContext:
    input_path: Path
    output_dir: Path
    raw_output_dir: Path | None = None
    baseline_markdown: Path | None = None
    emit_mermaid: bool = True
    copy_raw_outputs: bool = False
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class AdapterStatus:
    name: str
    available: bool
    detail: str = ""


@dataclass
class AdapterResult:
    adapter_name: str
    document: dict[str, Any]
    raw_outputs: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@dataclass
class RouteDecision:
    file_type: str
    backend_chain: list[str]
