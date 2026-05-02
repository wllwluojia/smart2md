from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from any2md_lib.config import load_config
from any2md_lib.models import ExtractionContext
from any2md_lib.normalizers import write_outputs
from any2md_lib.router import build_registry, decide_route, doctor


SUPPORTED_SUFFIXES = {".pdf", ".pptx", ".docx", ".xlsx", ".md", ".txt", ".ppt", ".doc", ".xls"}
LEGACY_SUFFIX_TARGET = {".ppt": ".pptx", ".doc": ".docx", ".xls": ".xlsx"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="smart2md",
        description="Structured document extraction for PDF, PPTX/PPT, DOCX/DOC, XLSX/XLS, and Markdown.",
        epilog=(
            "Common usage:\n"
            "  smart2md \"/abs/path/to/file-or-folder\" \"/abs/path/to/output-dir\"\n"
            "  smart2md doctor\n"
            "\n"
            "Outputs:\n"
            "  final readable files: original-filename.ext.md\n"
            "  backend raw artifacts are temporary by default and removed after extraction\n"
            "  debug files are disabled by default\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    extract = sub.add_parser(
        "extract",
        help="Extract one file or all supported files in a directory.",
        description="Run document extraction on a single file or recursively on a folder.",
    )
    extract.add_argument("input", nargs="?", help="Input file or directory path")
    extract.add_argument("output_dir", nargs="?", help="Output directory path")
    extract.add_argument("--input", dest="input_flag")
    extract.add_argument("--output-dir", dest="output_dir_flag")
    extract.add_argument("--backend", help="Override routing and use a specific backend directly (e.g. docling, mineru, markitdown, native-pptx, local-pdf).")
    extract.add_argument("--config", help="Optional config file path. Defaults to config/defaults.toml.")

    doctor_cmd = sub.add_parser(
        "doctor",
        help="Check backend availability.",
        description="Report which backends are available in the current environment.",
    )
    doctor_cmd.add_argument("--config", help="Optional config file path. Defaults to config/defaults.toml.")

    return parser.parse_args()


def iter_inputs(path: Path):
    if path.is_file():
        yield path
        return
    for candidate in sorted(path.rglob("*")):
        if candidate.is_file() and candidate.suffix.lower() in SUPPORTED_SUFFIXES:
            yield candidate


def compute_output_dirs(source_root: Path, candidate: Path, output_root: Path) -> tuple[Path, Path]:
    if source_root.is_file():
        relative_parent = Path()
    else:
        relative_parent = candidate.parent.relative_to(source_root)
    final_output_dir = output_root / relative_parent
    raw_output_dir = output_root / "_raw" / relative_parent / candidate.stem
    return final_output_dir, raw_output_dir


def _convert_with_soffice(source: Path, target_dir: Path, target_suffix: str) -> Path | None:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        return None
    target_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [soffice, "--headless", "--convert-to", target_suffix.lstrip("."), "--outdir", str(target_dir), str(source)],
        check=True,
        capture_output=True,
        text=True,
    )
    candidate = target_dir / f"{source.stem}{target_suffix}"
    return candidate if candidate.exists() else None


def _convert_with_textutil(source: Path, target_dir: Path, target_suffix: str) -> Path | None:
    textutil = shutil.which("textutil")
    if not textutil or target_suffix != ".docx":
        return None
    target_dir.mkdir(parents=True, exist_ok=True)
    candidate = target_dir / f"{source.stem}{target_suffix}"
    subprocess.run([textutil, "-convert", "docx", "-output", str(candidate), str(source)], check=True, capture_output=True, text=True)
    return candidate if candidate.exists() else None


def prepare_input(candidate: Path, candidate_output: Path) -> tuple[Path, list[str]]:
    suffix = candidate.suffix.lower()
    if suffix not in LEGACY_SUFFIX_TARGET:
        return candidate, []
    target_suffix = LEGACY_SUFFIX_TARGET[suffix]
    converted_dir = candidate_output / "_converted"
    converted = _convert_with_soffice(candidate, converted_dir, target_suffix)
    if converted:
        return converted, [f"Legacy {suffix} converted to {target_suffix} with LibreOffice."]
    converted = _convert_with_textutil(candidate, converted_dir, target_suffix)
    if converted:
        return converted, [f"Legacy {suffix} converted to {target_suffix} with textutil."]
    return candidate, [f"Legacy {suffix} conversion skipped: no compatible converter found. Falling back to direct routing."]


def run_extract(input_path: Path, output_dir: Path, config_path: Path | None, backend_override: str | None = None) -> list[dict[str, str]]:
    config = load_config(config_path)
    registry = build_registry()
    keep_raw_outputs = config.get("runtime", {}).get("keep_raw_outputs", False)
    results = []
    manifest = {"files": []}
    for candidate in iter_inputs(input_path):
        candidate_output, candidate_raw_output = compute_output_dirs(input_path, candidate, output_dir)
        prepared_input, pre_warnings = prepare_input(candidate, candidate_raw_output)
        context = ExtractionContext(
            input_path=prepared_input,
            output_dir=candidate_output,
            raw_output_dir=candidate_raw_output,
            emit_mermaid=config.get("runtime", {}).get("emit_mermaid", True),
            copy_raw_outputs=config.get("runtime", {}).get("copy_raw_outputs", False),
            config=config,
        )
        decision = decide_route(context, backend_override=backend_override)
        attempt_log = []
        success = None
        baseline_path = None
        for backend_name in decision.backend_chain:
            adapter = registry.get(backend_name)
            if adapter is None or not adapter.supports(decision.file_type):
                continue
            status = adapter.check(context)
            attempt_log.append({"backend": backend_name, "available": status.available, "detail": status.detail})
            if not status.available:
                continue
            try:
                adapter_result = adapter.extract(context)
                adapter_result.document["source_path"] = str(candidate)
                adapter_result.document["source_type"] = candidate.suffix.lower().lstrip(".")
                if prepared_input != candidate:
                    adapter_result.document["derived_input_path"] = str(prepared_input)
                warnings = list(adapter_result.document.get("warnings", []))
                warnings.extend(pre_warnings)
                if warnings:
                    adapter_result.document["warnings"] = warnings
                baseline = adapter_result.raw_outputs.get("baseline_markdown")
                baseline_path = Path(baseline) if baseline else None
                outputs = write_outputs(
                    adapter_result.document,
                    candidate_output,
                    baseline_path,
                    write_debug_outputs=config.get("runtime", {}).get("write_debug_outputs", False),
                )
                success = {
                    "input": str(candidate),
                    "backend": backend_name,
                    "outputs": {key: str(value) for key, value in outputs.items()},
                    "attempts": attempt_log,
                    "raw_outputs": adapter_result.raw_outputs if keep_raw_outputs else {},
                }
                break
            except Exception as exc:  # noqa: BLE001
                attempt_log.append({"backend": backend_name, "error": str(exc)})
                continue
        if success is None:
            success = {
                "input": str(candidate),
                "backend": "",
                "outputs": {},
                "attempts": attempt_log,
                "error": "No adapter succeeded.",
            }
        results.append(success)
        manifest["files"].append(success)
        if not keep_raw_outputs and candidate_raw_output.exists():
            shutil.rmtree(candidate_raw_output, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    if not keep_raw_outputs:
        shutil.rmtree(output_dir / "_raw", ignore_errors=True)
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return results


def run_doctor(config_path: Path | None) -> list[dict[str, str | bool]]:
    config = load_config(config_path)
    context = ExtractionContext(input_path=Path("."), output_dir=Path("."), config=config)
    return [{"name": item.name, "available": item.available, "detail": item.detail} for item in doctor(context)]


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).expanduser().resolve() if getattr(args, "config", None) else None
    if args.command == "doctor":
        print(json.dumps(run_doctor(config_path), ensure_ascii=False, indent=2))
        return 0
    input_path = args.input or args.input_flag
    output_dir = args.output_dir or args.output_dir_flag
    if not input_path or not output_dir:
        print("error: input and output-dir are required. Usage: smart2md extract INPUT OUTPUT_DIR [--backend NAME]", file=__import__("sys").stderr)
        return 1
    backend = getattr(args, "backend", None)
    results = run_extract(Path(input_path).expanduser().resolve(), Path(output_dir).expanduser().resolve(), config_path, backend_override=backend)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0
