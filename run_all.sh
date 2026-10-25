#!/usr/bin/env bash
# Rebuild everything from data/raw/extraction_packed.txt, then verify. Run from the project folder.
set -euo pipefail
cd "$(dirname "$0")/src"
python3 00_unpack_raw.py
python3 02_build_panel.py
python3 03_event_study.py > /dev/null
python3 04_robustness.py
python3 05_csa_pilot.py > /dev/null
python3 06_figures.py
python3 07_summary.py > /dev/null
echo "Done. See outputs/results.json and outputs/figures/."
echo "Verify with: python3 src/09_verify.py   (rebuild the paper with: bash paper/build.sh)"
