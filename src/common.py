"""Shared paths and constants for the Baltimore tree-planting & heat study."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
FIG = ROOT / "outputs" / "figures"
TAB = ROOT / "outputs" / "tables"
for d in (RAW, PROC, FIG, TAB):
    d.mkdir(parents=True, exist_ok=True)

CRS = "EPSG:32618"          # UTM 18N, the Landsat grid
CELL = 90                   # analysis cell size (m): 3x3 Landsat pixels
YEARS = list(range(2006, 2026))
BASE_YEARS = list(range(2006, 2010))   # pooled reference period for event studies
CAP = 10                    # counts per cell are capped here (≈99th percentile)

# Planting window implied by trunk size in the 2017-18 inventory (assumption;
# see docs/methods.md). Nursery stock goes in at ~1.5-2" caliper and young street
# trees add roughly 0.25-0.5" of diameter a year.
COHORTS = {
    "y15": "Young, DBH ≤ 1.5 in (planted ~2014–17)",
    "y30": "Young, DBH 1.5–3 in (planted ~2010–15)",
    "t36": "DBH 3–6 in (planted ~2003–11)",
}
