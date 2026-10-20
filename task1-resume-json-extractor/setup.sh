#!/usr/bin/env bash
# macOS / Linux / Git Bash
set -e
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
[ -f .env ] || cp .env.example .env
echo ""
echo "Done. Open .env and paste your GEMINI_API_KEY, then run:"
echo "  source venv/bin/activate && python test_connection.py"
