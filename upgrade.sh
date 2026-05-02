#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "Missing virtual environment. Run install.sh first." >&2
  exit 1
fi

source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip
python -m pip install --upgrade -r "${ROOT_DIR}/scripts/requirements.txt"
"${ROOT_DIR}/any2md" doctor
