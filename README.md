# Any2MD

Document orchestration layer for Hermes and Obsidian wiki ingestion.

This repository is meant to be publishable to GitHub as a standalone, installable package.

## Quick Start

If you downloaded this package from GitHub and want the fastest path to a working install:

```bash
cd Any2MD
bash install.sh
./any2md doctor
```

Then process a folder:

```bash
./any2md "/path/to/file-or-folder" "/path/to/output"
```

This package is designed so Hermes only needs one entrypoint. Users should not manually route files to Docling, MinerU, or other backends.

What it does:

- routes files by type and backend availability
- prefers local specialist tools such as Docling and MinerU
- keeps local fallbacks for PPTX and PDF
- normalizes outputs into one schema for downstream wiki ingestion
- supports install, doctor, and upgrade flows

Supported inputs:

- `pdf`
- `pptx`
- `docx`
- `xlsx`
- `md`
- legacy Office formats: `ppt`, `doc`, `xls`

Legacy Office handling:

- `ppt/doc/xls` are first converted to modern formats when a compatible converter is available
- preferred converter is `LibreOffice/soffice`
- `doc -> docx` can also use macOS `textutil`
- if conversion is unavailable, the router falls back to direct backend routing where possible

## Output Layers

Each processed source now has two different markdown roles:

- `original-filename.ext.md`: final human-readable output, intended for reading and wiki extraction
- `original-filename.structured.md`: debug / intermediate output with coordinates and machine-oriented detail

Recommended usage:

- read `*.ext.md`
- extract wiki content from `*.ext.md` or `.structured.json`
- keep `.structured.json` as the canonical machine trace
- treat backend-native raw artifacts as debug assets under `_raw/`

## Core Commands

```bash
bash install.sh
bash doctor.sh
./any2md "/path/to/file-or-folder" "/path/to/output"
```

## One-Step Install

Default install is now online and bootstrap-style:

```bash
bash install.sh
```

This creates `.venv` and installs the recommended local set by default:

- router requirements
- `docling`
- `mineru`
- `markitdown`
- `PyMuPDF`

If your machine already has `docling`, `mineru`, or `markitdown` on `PATH`, the installer reuses them by default instead of reinstalling them. PDF routing now uses local PyMuPDF signals and `pymupdf4llm` for the fast path.

Lighter setup:

```bash
bash install.sh --with-backends core
```

This installs only:

- `markitdown`
- `PyMuPDF`

Optional install modes:

```bash
bash install.sh --with-backends core
bash install.sh --with-backends full
bash install.sh --with-backends docling,mineru,pymupdf
bash install.sh --force-install --with-backends recommended
```

Archive fallback mode is also supported for offline or controlled installs:

```bash
bash install.sh --from-archive /path/to/downloads --with-backends recommended
```

## GitHub Release Notes

This repository is intended to be publishable as a standalone package.

Recommended release contents:

- `README.md`
- `LICENSE`
- `install.sh`
- `upgrade.sh`
- `doctor.sh`
- `config/`
- `scripts/`
- `references/`
- `.github/workflows/smoke-test.yml`

Recommended first release promise:

- one-step install
- short command entrypoint: `any2md <input> <output-dir>`
- stable CLI
- config-driven routing
- local-first defaults
- no cloud-auth dependency by default

### What the installer does

- creates a local virtual environment under `.venv`
- installs Python requirements for the router itself
- installs selected backends from official package sources by default
- leaves Hermes with one stable command surface

### Backend presets

- `core`: `markitdown`, `PyMuPDF`
- `recommended`: `docling`, `mineru`, `markitdown`, `PyMuPDF`, `pymupdf4llm`
- `full`: same as `recommended` for now, reserved for future expansion

Install strategy:

- default: install `core`
- reuse existing system tools when available
- use `--force-install` if you explicitly want to vendor your own copies into this package environment

### Backend names

- `docling`: installs the official `docling` Python package
- `mineru`: installs `uv`, then installs `mineru[all]`
- `markitdown`: installs the baseline text converter
- `pymupdf`: installs `PyMuPDF` and `pymupdf4llm`

Notes from upstream docs:

- Docling is officially installable with `pip install docling`.
- MinerU documents `uv pip install -U "mineru[all]"` for local deployment.

## Default Routing Rules

Current default routing is:

- `pdf -> PyMuPDF judge -> fast: pymupdf4llm, standard: docling, complex/scanned: mineru`
- `docx -> docling -> markitdown`
- `pptx -> mineru -> native-pptx -> markitdown`
- `xlsx -> mineru -> markitdown`
- `md/txt/default -> markitdown`

Legacy routing behavior:

- `ppt -> convert to pptx -> pptx chain`
- `doc -> convert to docx -> docx chain`
- `xls -> convert to xlsx -> xlsx chain`
- if conversion fails, the file falls back to the default chain for its raw extension

## Current Adapters

- `mineru`
- `pymupdf4llm`
- `docling`
- `native-pptx`
- `local-pdf`
- `markitdown`

## Output Contract

Each processed file produces:

- `*.structured.json`
- `*.structured.md`
- `*.ext.md` as the final readable markdown named after the original source file
- `*.mermaid.md`
- `_raw/<relative-source-path>/<file-stem>/...` for backend-native intermediate artifacts when a backend emits them
- `manifest.json` at the batch output root

The routing table lives in [`config/defaults.toml`](config/defaults.toml).

## Repository Layout

```text
Any2MD/
├── README.md
├── LICENSE
├── install.sh
├── upgrade.sh
├── doctor.sh
├── config/
├── references/
├── scripts/
└── .github/workflows/
```

## Release Checklist

Before pushing to GitHub, verify:

- `bash install.sh --with-backends core`
- `bash doctor.sh`
- `bash scripts/smoke_test.sh`
- `./any2md doctor`
- `config/defaults.toml` matches the intended default routing
- `README.md` reflects the current supported formats and installation modes

To build a shareable release archive locally:

```bash
bash scripts/create_release_bundle.sh
```

This creates a versionless zip under `dist/` that can be attached to a GitHub release.
