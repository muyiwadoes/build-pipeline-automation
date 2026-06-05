#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Setting up virtual environment"
python3 -m venv .venv
source .venv/bin/activate

echo "==> Installing dependencies"
pip install --quiet -r requirements.txt -r requirements-dev.txt

echo "==> Running pipeline"
PYTHONPATH="$ROOT" python -m src.pipeline
echo "==> Pipeline completed successfully"