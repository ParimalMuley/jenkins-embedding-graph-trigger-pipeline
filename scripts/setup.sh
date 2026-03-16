#!/usr/bin/env bash
set -euo pipefail
 
# Install python3-venv if missing — safe to run even if already installed
if ! python3 -m venv --help > /dev/null 2>&1; then
    echo "Installing python3-venv..."
    sudo apt-get install -y -qq python3.10-venv python3-pip
fi
 
echo "Creating virtual environment..."
mkdir -p "${ARTIFACTS_DIR}"
python3 -m venv "${PYTHON_VENV}"
. "${PYTHON_VENV}/bin/activate"
 
echo "Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
 
echo "Setup complete.
