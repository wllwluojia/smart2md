#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

bash "${ROOT_DIR}/install.sh" --with-backends core
source "${ROOT_DIR}/.venv/bin/activate"
"${ROOT_DIR}/smart2md" doctor

cat <<EOF
smoke test passed
root=${ROOT_DIR}
EOF
