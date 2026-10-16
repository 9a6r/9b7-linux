#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
export UV_CACHE_DIR=/workspace/.cache/9b7-uv
uv venv --allow-existing .venv
uv pip install --python .venv/bin/python --require-hashes -r requirements.lock
uv pip install --python .venv/bin/python --no-deps -e .
# Some cloud editors create new public source files as 0600. Containers use other UIDs.
chmod a+r services/*.conf services/*.py
export PATH="$PWD/.venv/bin:$PATH"
bash scripts/check.sh
QT_QPA_PLATFORM=offscreen .venv/bin/python tests/gui_smoke.py
