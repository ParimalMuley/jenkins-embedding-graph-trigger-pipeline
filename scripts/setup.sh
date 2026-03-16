#!/usr/bin/env bash
set -euo pipefail
 
echo "--- Python diagnostics ---"
which python3
python3 --version
python3 -c "import sys; print('sys.prefix:', sys.prefix)"
apt list --installed 2>/dev/null | grep -i python || true
echo "--------------------------"
 
echo "Installing python3.10-venv and pip explicitly..."
sudo apt-get install -y -qq python3.10-venv python3.10-distutils python3-pip || \
sudo apt-get install -y -qq python3-venv python3-pip
 
echo "Creating virtual environment..."
mkdir -p "${ARTIFACTS_DIR}"
python3 -m venv --clear "${PYTHON_VENV}"
. "${PYTHON_VENV}/bin/activate"
 
echo "Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
 
echo "Setup complete."
