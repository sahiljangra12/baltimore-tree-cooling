"""Pilot design B: neighborhood (Community Statistical Area) panel.

Dose = TreeBaltimore trees planted 2013-2020 per km² (BNIA / Open Baltimore).
Outcome = CSA mean of the 90 m cell LST anomalies (weighted by clear scenes).
Event study: LST[c,t] = a_c + d_t + sum_t b_t * Dose_c * 1[year=t] + e, base 2006-2008 (2009-2012 are pre-period checks),
SEs clustered by CSA (55 clusters). Coarse and low-powered by design: a check on
the direction of the cell-level result, not the main estimate.
"""
import json
import numpy as np
import pandas as pd
import pyfixest as pf
from shapely.geometry import shape, Point
from common import PROC, RAW, TAB

gj = json.load(open(RAW / "csa_plantings_2013_2020.geojson"))
rows = []
for f in gj["features"]:
    p = f["properties"]; g = shape(f["geometry"])
    tot = sum((p.get(f"treeplnt{y}") or 0) for y in range(13, 21))
    rows.append({"csa": p["CSA2020"], "area_km2": g.area / 1e6, "planted_2013_2020": tot, "geom": g})
csa = pd.DataFrame(rows)
csa["dose_per_km2"] = csa.planted_2013_2020 / csa.area_km2

df = pd.read_csv(PROC / "analysis_panel.csv")
cells = df.drop_duplicates("cell_id")[["cell_id", "x", "y"]]
def which(x, y):
    pt = Point(x, y)
    for n, g in zip(csa.csa, csa.geom):
        if g.contains(pt):
            return n
cells["csa"] = [which(x, y) for x, y in zip(cells.x, cells.y)]
df = df.merge(cells[["cell_id", "csa"]], on="cell_id").dropna(subset=["csa"])
df["wy"] = df.lst_anom * df.n_scenes
panel = df.groupby(["csa", "year"]).agg(wy=("wy", "sum"), w=("n_scenes", "sum"), n_cells=("cell_id", "nunique")).reset_index()
panel["lst_anom"] = panel.wy / panel.w
panel = panel.merge(csa[["csa", "dose_per_km2", "planted_2013_2020", "area_km2"]], on="csa")
panel["dose100"] = panel.dose_per_km2 / 100          # per 100 trees/km²
panel["ybin"] = np.where(panel.year <= 2008, "base", panel.year.astype(str))
panel.to_csv(PROC / "csa_panel.csv", index=False)

fit = pf.feols("lst_anom ~ i(ybin, dose100, ref='base') | csa + year", data=panel,
               vcov={"CRV1": "csa"})
t = fit.tidy().reset_index()
t["year"] = t.Coefficient.str.extract(r"(\d{4})").astype(int)
t = t[["year", "Estimate", "Std. Error", "2.5%", "97.5%"]]
t.to_csv(TAB / "csa_event_study.csv", index=False)
late = t[t.year >= 2021]; pre = t[t.year <= 2012]
from scipy import stats
idx = list(fit.coef().index); pn = [n for n in idx if any(f"{y}" in n for y in range(2009, 2013))]
R = np.zeros((len(pn), len(idx)))
for r, n in enumerate(pn): R[r, idx.index(n)] = 1
bb = R @ fit.coef().values; VV = R @ fit._vcov @ R.T; wald = float(bb @ np.linalg.solve(VV, bb))
summ = {"n_csa": int(panel.csa.nunique()), "years": [int(panel.year.min()), int(panel.year.max())],
        "dose_mean_per_km2": round(float(csa.dose_per_km2.mean()), 1),
        "dose_range_per_km2": [round(float(csa.dose_per_km2.min()), 1), round(float(csa.dose_per_km2.max()), 1)],
        "trees_2013_2020_total": int(csa.planted_2013_2020.sum()),
        "mean_coef_2021_2025_per_100_trees_km2": round(float(late.Estimate.mean()), 4),
        "share_2021_2025_coefs_negative": round(float((late.Estimate < 0).mean()), 2),
        "mean_coef_2009_2012_pre": round(float(pre.Estimate.mean()), 4),
        "pretrend_wald_2009_2012": round(wald, 2), "pretrend_p": round(float(1 - stats.chi2.cdf(wald, len(pn))), 4)}
json.dump(summ, open(TAB / "csa_pilot.json", "w"), indent=1)
print(t.round(3).to_string(index=False)); print(summ)
