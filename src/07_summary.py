"""Collect headline numbers into outputs/results.json (the README and paper cite these)."""
import json
import pandas as pd
from common import ROOT, RAW, PROC, TAB

es = json.load(open(TAB / "event_study_main.json"))
rb = json.load(open(TAB / "robustness.json"))
csa = json.load(open(TAB / "csa_pilot.json"))
sc = pd.read_csv(RAW / "landsat_scenes.csv")
cells = pd.read_csv(RAW / "cells_inventory.csv")
r = {
    "data": {"cells_90m": int(len(cells)), "cell_years": int(es["n_obs"]), "neighborhoods": int(es["n_clusters"]),
             "scenes_searched": int(len(sc)), "scenes_used": int((sc.used.astype(str).str.lower() == "true").sum()),
             "scene_read_errors": int((sc.used.astype(str) == "read_error").sum()),
             "young_trees_le_1_5in": int(cells.y15.sum()), "young_trees_1_5_3in": int(cells.y30.sum()),
             "trees_3_6in": int(cells.t36.sum()), "mature_gt_6in": int(cells.mat.sum()), "vacant_street_sites": int(cells.vac.sum())},
    "main_2022_25_vs_2006_09_per_tree": {k: es[k]["2022_2025"] for k in ("y15", "y30", "t36", "vac")},
    "pretrend_y15": rb["pretrend_y15_2010_2013"],
    "robustness_y15_2022_25": {k: v["y15"] for k, v in rb.items() if isinstance(v, dict) and "y15" in v},
    "placebo_not_suitable_sites": rb["placebo_not_suitable"],
    "binary_young_vs_vacant_cells": rb["binary_young_vs_vacant"],
    "long_difference_sensitivity": rb["long_difference_y15"],
    "csa_pilot": csa,
}
json.dump(r, open(ROOT / "outputs" / "results.json", "w"), indent=1)
print(json.dumps(r["data"])); print(json.dumps(r["main_2022_25_vs_2006_09_per_tree"], indent=0)[:900])
