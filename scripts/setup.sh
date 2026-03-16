#!/usr/bin/env bash
set -euo pipefail

echo "Creating virtual environment"
mkdir -p "${ARTIFACTS_DIR}"
python3 -m venv "${PYTHON_VENV}"
. "${PYTHON_VENV}/bin/activate"

echo "Installing dependencies"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo "Setup complete."
