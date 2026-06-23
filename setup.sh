#!/usr/bin/env bash
# One-command setup for macOS / Linux
set -euo pipefail

RUN_DEMO=false
for arg in "$@"; do
  if [[ "$arg" == "--demo" ]]; then
    RUN_DEMO=true
  fi
done

python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -r requirements-dev.txt

if $RUN_DEMO; then
  python main.py --demo
fi

echo "Done. Activate with: source .venv/bin/activate"
echo "Streamlit: streamlit run app.py"
