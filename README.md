# smart2md

> **Intelligent Document Orchestration for AI-Ready Knowledge Bases.**
> Stop wrestling with messy parsers. smart2md auto-routes every document to the best-in-class backend, delivering **structured, compact, and high-quality Markdown** — perfectly tuned for Obsidian, NotebookLM, and RAG pipelines.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Why smart2md?

Most document-to-Markdown tools pick **one parser and call it a day**. That works fine — until you throw a scanned PDF, a complex spreadsheet, and a dense PowerPoint at it. Then it falls apart.

**smart2md is different.** It's an orchestration layer, not just a converter.

| | Typical Single-Backend Tool | **smart2md** |
|---|---|---|
| **Parser Strategy** | One-size-fits-all | Auto-routes to best-in-class backend per file type |
| **Output Quality** | Raw text dump | Structured, compact, wiki-ready Markdown |
| **AI Readiness** | Needs manual cleanup | Normalized schema, optimized for RAG & vector ingestion |
| **Privacy** | Often requires cloud API | Local-first, no cloud auth dependency by default |
| **Install UX** | Manual dependency wrangling | One-step `install.sh` + `doctor.sh` health check |
| **Folder Handling** | File-by-file only | Mirrors full directory tree structure in output |

---

## ✨ Core Strengths

### 🧠 Intelligent Multi-Backend Routing
smart2md doesn't blindly push every file to the same parser. Its routing engine reads the file type and your local environment, then dispatches each document to the most appropriate specialist tool:
- **Docling** (IBM Research) for complex PDFs and DOCX
- **MinerU** (OpenDataLab) for scanned PDFs and PPTX
- **pymupdf4llm** for fast-path PDF extraction
- **MarkItDown** (Microsoft) as a reliable universal fallback

### 📐 Structured, Compact, High-Quality Output
Raw text extraction is not enough for serious AI pipelines. smart2md's normalizer produces:
- **Clean heading hierarchy** — no orphaned fragments, no duplicated titles
- **Compact table formatting** — standard Markdown tables, not sprawling ASCII art
- **Deduplicated content** — headers, footers, and repeated boilerplate are stripped
- **Readable paragraphs** — sentence boundaries are preserved, no mid-sentence line breaks

### 📂 Directory-Preserving Batch Processing
Process an entire knowledge base folder at once. The output mirrors the **exact same folder structure** as the input — no flattening, no renaming. Drop it straight into Obsidian or a RAG ingestion pipeline.

### 🔒 Local-First, Privacy-Preserving
All processing runs on your machine. No files are sent to external APIs by default. Ideal for sensitive enterprise documents or personal knowledge bases.

### ⚡ One-Step Install with Health Check
```bash
bash install.sh
./smart2md doctor
```
The installer auto-detects tools already on your system and reuses them. The `doctor` command validates your environment in seconds.

---

## 🚀 Quick Start

```bash
git clone https://github.com/wllwluojia/smart2md.git
cd smart2md
bash install.sh
./smart2md doctor
```

**Convert a single file:**
```bash
./smart2md "/path/to/document.pdf" "/path/to/output_dir"
```

**Batch-convert an entire folder (preserving structure):**
```bash
./smart2md "/path/to/knowledge_base/" "/path/to/output_dir"
```

---

## 📄 Supported Inputs

| Format | Extension | Notes |
|---|---|---|
| PDF | `pdf` | Smart routing: fast / standard / scanned-OCR paths |
| PowerPoint | `pptx`, `ppt` | Legacy `.ppt` auto-converted before processing |
| Word | `docx`, `doc` | Legacy `.doc` auto-converted before processing |
| Excel | `xlsx`, `xls` | Legacy `.xls` auto-converted before processing |
| Plain Text | `txt` | Normalized and structured for wiki ingestion |
| Markdown | `md` | Pass-through with normalization and cleanup |

---

## 📦 Output Structure

Each processed file produces a clean set of outputs:

```
output_dir/
├── document.pdf.md          ← Human-readable, wiki-ready Markdown
├── document.structured.md   ← Machine-readable with layout metadata
├── document.structured.json ← Canonical structured trace for AI pipelines
├── document.mermaid.md      ← Diagram extraction (where applicable)
└── _raw/                    ← Backend-native intermediate artifacts
```

**Recommended usage:**
- Use `*.pdf.md` for human reading, Obsidian notes, and NotebookLM ingestion
- Use `*.structured.json` for RAG vector indexing and deep AI analysis
- Archive `_raw/` as debug assets

---

## ⚙️ Install Options

**Default (recommended):**
```bash
bash install.sh
```
Installs: `docling`, `mineru`, `markitdown`, `PyMuPDF`, `pymupdf4llm`

**Lightweight (core only):**
```bash
bash install.sh --with-backends core
```
Installs: `markitdown`, `PyMuPDF`

**Offline / archive mode:**
```bash
bash install.sh --from-archive /path/to/downloads --with-backends recommended
```

---

## 🔀 Default Routing Rules

| Input | Primary Backend | Fallback |
|---|---|---|
| `pdf` (digital) | `pymupdf4llm` (fast) → `docling` (standard) | `markitdown` |
| `pdf` (scanned) | `mineru` | `local-pdf` |
| `docx` | `docling` | `markitdown` |
| `pptx` | `mineru` → `native-pptx` | `markitdown` |
| `xlsx` | `mineru` | `markitdown` |
| `txt` / `md` | `markitdown` | — |

Routing rules are fully configurable in [`config/defaults.toml`](config/defaults.toml).

---

## 🗂️ Repository Layout

```
smart2md/
├── README.md
├── README_ZH.md
├── LICENSE
├── install.sh
├── upgrade.sh
├── doctor.sh
├── smart2md              ← CLI entrypoint
├── config/
│   └── defaults.toml
├── references/
├── scripts/
│   ├── smart2md_cli_main.py
│   └── smart2md_lib/
└── .github/workflows/
```

---

## 🤝 Contributing & License

Contributions are welcome! Feel free to open Issues or Pull Requests.

This project is licensed under the [MIT License](LICENSE).
