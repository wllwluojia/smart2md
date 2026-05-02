#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"
STAGE_DIR="${DIST_DIR}/Any2MD"
ARCHIVE_PATH="${DIST_DIR}/Any2MD.zip"

rm -rf "${STAGE_DIR}" "${ARCHIVE_PATH}"
mkdir -p "${STAGE_DIR}"

rsync -a \
  --exclude '.git/' \
  --exclude '.DS_Store' \
  --exclude '.github/workflows/*.log' \
  --exclude '.venv/' \
  --exclude '.vendor/' \
  --exclude '__pycache__/' \
  --exclude 'dist/' \
  --exclude '{agents,references,scripts}/' \
  --exclude '*.pyc' \
  --exclude '*.pyo' \
  "${ROOT_DIR}/" "${STAGE_DIR}/"

chmod +x \
  "${STAGE_DIR}/any2md" \
  "${STAGE_DIR}/install.sh" \
  "${STAGE_DIR}/upgrade.sh" \
  "${STAGE_DIR}/doctor.sh" \
  "${STAGE_DIR}/scripts/smoke_test.sh" \
  "${STAGE_DIR}/scripts/create_release_bundle.sh"

(
  cd "${DIST_DIR}"
  zip -qr "${ARCHIVE_PATH}" "Any2MD"
)

echo "release bundle created:"
echo "  ${ARCHIVE_PATH}"
