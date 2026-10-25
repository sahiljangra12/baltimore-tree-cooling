#!/bin/bash
# Regenerate macros/tables from outputs, inline the tables, compile the PDF.
set -e
cd "$(dirname "$0")"
python3 ../src/08_tex.py
python3 - <<'PY'
import re
t = open("main.tex").read()
t = re.sub(r"\\input\{(tab_[a-z]+\.tex)\}", lambda m: open(m.group(1)).read().rstrip("\n"), t)
open("paper_build.tex", "w").write(t)
PY
latexmk -pdf -interaction=nonstopmode -quiet paper_build.tex >/dev/null 2>&1 || true
cp paper_build.pdf Baltimore_Street_Trees_Cooling_Sahil_2026.pdf
latexmk -c paper_build.tex >/dev/null 2>&1 || true
echo "Built paper/Baltimore_Street_Trees_Cooling_Sahil_2026.pdf"
