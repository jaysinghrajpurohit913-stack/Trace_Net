#!/usr/bin/env bash
# Run this to start TraceNet on Mac / Linux:  bash start.sh
cd "$(dirname "$0")"
command -v python3 >/dev/null || { echo "Install Python 3.10+ first."; exit 1; }
if [ ! -d .venv ]; then
  echo "First time setup, this takes a few minutes..."
  python3 -m venv .venv && . .venv/bin/activate && pip install -q -r requirements.txt
else
  . .venv/bin/activate
fi
streamlit run app.py
