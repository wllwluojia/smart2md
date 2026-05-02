#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

if [[ -d "${VENV_DIR}" ]]; then
  source "${VENV_DIR}/bin/activate"
fi

"${ROOT_DIR}/smart2md" doctor
