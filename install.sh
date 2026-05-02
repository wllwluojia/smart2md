#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"
NPM_BIN="${NPM_BIN:-npm}"
MODE="online"
WITH_BACKENDS="${WITH_BACKENDS:-recommended}"
ARCHIVES_DIR=""
REUSE_SYSTEM_TOOLS="${REUSE_SYSTEM_TOOLS:-1}"

usage() {
  cat <<EOF
Usage:
  bash install.sh [--with-backends core|recommended|full|list] [--from-archive DIR] [--force-install]

Defaults:
  --with-backends recommended
  online install from official package sources
  reuse already-installed system tools when possible

Examples:
  bash install.sh
  bash install.sh --with-backends core
  bash install.sh --with-backends full
  bash install.sh --with-backends docling,mineru,pymupdf
  bash install.sh --from-archive /Users/me/Downloads --with-backends recommended
  bash install.sh --force-install --with-backends recommended
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-backends)
      WITH_BACKENDS="${2:-}"
      shift 2
      ;;
    --from-archive)
      MODE="archive"
      ARCHIVES_DIR="${2:-}"
      shift 2
      ;;
    --force-install)
      REUSE_SYSTEM_TOOLS="0"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

require_cmd() {
  local name="$1"
  if ! command -v "${name}" >/dev/null 2>&1; then
    echo "Missing required command: ${name}" >&2
    exit 1
  fi
}

command_exists_anywhere() {
  local name="$1"
  if [[ -x "${VENV_DIR}/bin/${name}" ]]; then
    return 0
  fi
  command -v "${name}" >/dev/null 2>&1
}

python_has_module() {
  local module="$1"
  python - <<EOF >/dev/null 2>&1
import importlib.util
raise SystemExit(0 if importlib.util.find_spec("${module}") else 1)
EOF
}

skip_or_install_message() {
  local backend="$1"
  local detail="$2"
  echo "[install] reusing existing ${backend}: ${detail}"
}

install_markitdown() {
  if [[ "${REUSE_SYSTEM_TOOLS}" == "1" ]] && command_exists_anywhere "markitdown"; then
    skip_or_install_message "markitdown" "$(command -v markitdown || echo "${VENV_DIR}/bin/markitdown")"
    return 0
  fi
  python -m pip install markitdown
}

install_docling() {
  if [[ "${REUSE_SYSTEM_TOOLS}" == "1" ]] && command_exists_anywhere "docling"; then
    skip_or_install_message "docling" "$(command -v docling || echo "${VENV_DIR}/bin/docling")"
    return 0
  fi
  python -m pip install docling
}

install_mineru() {
  if [[ "${REUSE_SYSTEM_TOOLS}" == "1" ]] && command_exists_anywhere "mineru"; then
    skip_or_install_message "mineru" "$(command -v mineru || echo "${VENV_DIR}/bin/mineru")"
    return 0
  fi
  python -m pip install uv
  "${VENV_DIR}/bin/uv" pip install -U "mineru[all]"
}

install_pymupdf() {
  if python_has_module "fitz" && python_has_module "pymupdf4llm"; then
    skip_or_install_message "PyMuPDF" "PyMuPDF and pymupdf4llm available in current virtualenv"
    return 0
  fi
  python -m pip install PyMuPDF pymupdf4llm
}

archive_install_docling() {
  local src="${ARCHIVES_DIR}/docling-main"
  python -m pip install -e "${src}"
}

archive_install_mineru() {
  local src="${ARCHIVES_DIR}/MinerU-master"
  python -m pip install uv
  "${VENV_DIR}/bin/uv" pip install -e "${src}[all]"
}

prepare_archives() {
  if [[ -z "${ARCHIVES_DIR}" ]]; then
    echo "--from-archive requires a directory argument." >&2
    exit 1
  fi
  require_cmd unzip
  mkdir -p "${ROOT_DIR}/.vendor/src"
  unzip -oq "${ARCHIVES_DIR}/docling-main.zip" -d "${ROOT_DIR}/.vendor/src"
  unzip -oq "${ARCHIVES_DIR}/MinerU-master.zip" -d "${ROOT_DIR}/.vendor/src"
  ARCHIVES_DIR="${ROOT_DIR}/.vendor/src"
}

run_backend_install() {
  local backend="$1"
  case "${backend}" in
    core)
      install_markitdown
      install_pymupdf
      ;;
    recommended)
      install_markitdown
      install_pymupdf
      if [[ "${MODE}" == "online" ]]; then
        install_docling
        install_mineru
      else
        archive_install_docling
        archive_install_mineru
      fi
      ;;
    full)
      install_markitdown
      install_pymupdf
      if [[ "${MODE}" == "online" ]]; then
        install_docling
        install_mineru
      else
        archive_install_docling
        archive_install_mineru
      fi
      ;;
    docling)
      [[ "${MODE}" == "online" ]] && install_docling || archive_install_docling
      ;;
    mineru)
      [[ "${MODE}" == "online" ]] && install_mineru || archive_install_mineru
      ;;
    markitdown)
      install_markitdown
      ;;
    pymupdf)
      install_pymupdf
      ;;
    *)
      echo "Unknown backend: ${backend}" >&2
      exit 1
      ;;
  esac
}

require_cmd "${PYTHON_BIN}"
if [[ "${MODE}" == "archive" ]]; then
  prepare_archives
fi

if [[ ! -d "${VENV_DIR}" ]]; then
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi
source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "${ROOT_DIR}/scripts/requirements.txt"

if [[ "${WITH_BACKENDS}" == *","* ]]; then
  IFS=',' read -r -a BACKENDS <<< "${WITH_BACKENDS}"
  for backend in "${BACKENDS[@]}"; do
    run_backend_install "${backend}"
  done
else
  run_backend_install "${WITH_BACKENDS}"
fi

cat <<EOF
Any2MD installed in:
  ${VENV_DIR}

Next:
  1. Activate: source "${VENV_DIR}/bin/activate"
  2. Run doctor: "${ROOT_DIR}/any2md" doctor
  3. Configure external backends in:
     ${ROOT_DIR}/config/defaults.toml
  4. Installation mode:
     mode=${MODE}
     backends=${WITH_BACKENDS}
     reuse_system_tools=${REUSE_SYSTEM_TOOLS}
  5. Extract example:
     "${ROOT_DIR}/any2md" "/abs/path/to/input" "/abs/path/to/output"
EOF
