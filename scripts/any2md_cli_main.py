#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from any2md_lib.cli import main  # noqa: E402


HELP_TEXT = """any2md: structured document extraction CLI

Usage:
  any2md <input-path> <output-dir>
  any2md extract --input <input-path> --output-dir <output-dir> [--config <path>]
  any2md doctor [--config <path>]
  any2md -h | --help

Examples:
  any2md "/abs/path/to/file.pptx" "/abs/path/to/output"
  any2md "/abs/path/to/folder" "/abs/path/to/output"
  any2md doctor

What it writes:
  - original-filename.ext.md
  - *.structured.json
  - *.structured.md
  - *.mermaid.md
  - _raw/ (backend-native intermediate artifacts when present)
"""


if __name__ == "__main__":
    argv = sys.argv[1:]
    if not argv or argv[0] in {"-h", "--help", "help"}:
        print(HELP_TEXT)
        raise SystemExit(0)
    if argv and argv[0] != "doctor" and argv[0] != "extract" and not argv[0].startswith("-"):
        if len(argv) != 2:
            print(HELP_TEXT)
            raise SystemExit(1)
        sys.argv = [sys.argv[0], "extract", "--input", argv[0], "--output-dir", argv[1]]
    raise SystemExit(main())
