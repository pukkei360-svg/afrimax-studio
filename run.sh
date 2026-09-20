#!/usr/bin/env bash
# Afrimax-Studio one-command pipeline (resumable — safe to re-run).
set -e
cd "$(dirname "$0")"
python3 gen_keyframes.py
python3 voiceover.py
python3 animate.py
python3 make_cards.py
python3 assemble.py
python3 qc.py
