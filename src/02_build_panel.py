"""Merge the cell inventory with the cell-year surface-temperature panel.

Inputs (data/raw/):
  cells_inventory.csv        one row per 90 m cell: counts of street-tree inventory
                             records by type (2017-18 Baltimore Forestry inventory)
  panel_cell_year_lst.csv    cell x year mean summer LST anomaly (°C vs scene median)
Output:
  data/processed/analysis_panel.csv
"""
import numpy as np
import pandas as pd
from common import RAW, PROC, CAP, BASE_YEARS

cells = pd.read_csv(RAW / "cells_inventory.csv")
panel = pd.read_csv(RAW / "panel_cell_year_lst.csv")

counts = ["y15", "y30", "t36", "mat", "vac", "vacpot", "vacns", "stump", "dead", "park"]
for c in counts:
    cells[f"{c}_c"] = cells[c].clip(upper=CAP)
cells["young"] = cells.y15 + cells.y30
cells["street_sites"] = cells[["y15", "y30", "t36", "mat", "vac", "vacpot", "vacns", "stump", "dead"]].sum(axis=1)

cells["neighborhood"] = cells.neighborhood.fillna("(no name)")
df = panel.merge(cells, on="cell_id", how="left")
df["nb_year"] = df.neighborhood + "_" + df.year.astype(str)
df["ybin"] = np.where(df.year.isin(BASE_YEARS), "base", df.year.astype(str))
df.to_csv(PROC / "analysis_panel.csv", index=False)
print(f"{df.cell_id.nunique():,} cells, {len(df):,} cell-years, "
      f"{df.neighborhood.nunique()} neighborhoods, years {df.year.min()}-{df.year.max()}")
