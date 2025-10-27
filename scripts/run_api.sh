#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="$(pwd):${PYTHONPATH:-}"
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
