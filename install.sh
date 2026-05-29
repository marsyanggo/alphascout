#!/usr/bin/env bash
# Set up the yfinance backend's virtualenv. Run once after cloning.
set -euo pipefail
cd "$(dirname "$0")"

echo "Creating .venv ..."
python3 -m venv .venv
.venv/bin/python -m pip install --quiet --upgrade pip
echo "Installing requirements ..."
.venv/bin/python -m pip install --quiet -r requirements.txt
echo "Done. yfinance backend ready:"
.venv/bin/python -c "import yfinance as yf; print('  yfinance', yf.__version__)"
echo
echo "Optional: copy .env.example to .env and add API keys for the"
echo "Financial Datasets (fd.py) and Finnhub (finnhub.py) backends."
