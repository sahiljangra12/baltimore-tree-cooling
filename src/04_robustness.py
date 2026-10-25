"""Robustness checks for the event study (03_event_study.py).

Each check re-estimates the pooled change in surface temperature per young tree
(DBH <= 1.5 in) between the base period 2006-09 and 2022-25, plus the same for
the 1.5-3 in and 3-6 in cohorts. Also: a pre-trend joint test, a binary
treated-vs-vacant comparison, a placebo, coarser clustering, and a long-difference
regression with Cinelli & Hazlett (2020) sensitivity to unobserved confounding.
"""
import gc
import json
import warnings
import numpy as np
import pandas as pd
import pyfixest as pf
import statsmodels.formula.api as smf
from shapely.geometry import shape, Point
from common import PROC, RAW, TAB

warnings.filterwarnings("ignore")
df = pd.read_csv(PROC / "analysis_panel.csv")
scenes = pd.read_csv(RAW / "landsat_scenes.csv")

# Community Statistical Area (55 units) for coarser clustering
gj = json.load(open(RAW / "csa_plantings_2013_2020.geojson"))
polys = [(f["properties"]["CSA2020"], shape(f["geometry"])) for f in gj["features"]]
cells = df.drop_duplicates("cell_id")[["cell_id", "x", "y"]]
def csa_of(x, y):
    p = Point(x, y)
    for name, g in polys:
        if g.contains(p):
            return name
    return None
cells["csa"] = [csa_of(x, y) for x, y in zip(cells.x, cells.y)]
df = df.merge(cells[["cell_id", "csa"]], on="cell_id")
df["csa"] = df.csa.fillna("outside")

LATE = [2022, 2023, 2024, 2025]
def late_effect(fit, var):
    coefs = fit.coef(); V = fit._vcov; idx = list(coefs.index)
    names = [n for n in idx if n.endswith(f":{var}_c") and any(f"[T.{y}]" in n or f"::{y}:" in n for y in LATE)]
    w = np.zeros(len(idx))
    for n in names: w[idx.index(n)] = 1 / len(names)
    b = float(w @ coefs.values); se = float(np.sqrt(w @ V @ w))
    return {"b": round(b, 4), "se": round(se, 4), "lo": round(b - 1.96 * se, 4), "hi": round(b + 1.96 * se, 4)}

def run(data, fe="cell_id + nb_year", vcov={"CRV1": "neighborhood"}, weights="n_scenes",
        treat=("y15", "y30", "t36"), controls=("vac", "mat", "stump"), keep=False):
    terms = [f"i(ybin, {v}_c, ref='base')" for v in list(treat) + list(controls)]
    fit = pf.feols("lst_anom ~ " + " + ".join(terms) + f" | {fe}", data=data,
                   weights=weights, vcov=vcov)
    res = {v: late_effect(fit, v) for v in treat}
    if keep:
        return fit, res
    del fit; gc.collect()
    return None, res

out = {}
fit0, out["main"] = run(df, keep=True)

# 1. Pre-trend joint test: y15 coefficients 2010-2017 all zero (planted ~2014-17,
#    so any pre-2014 movement is a red flag; 2014-17 is partly treated).
idx = list(fit0.coef().index)
pre = [n for n in idx if n.endswith(":y15_c") and any(f"{y}" in n for y in range(2010, 2014))]
R = np.zeros((len(pre), len(idx)))
for r, n in enumerate(pre): R[r, idx.index(n)] = 1
b = R @ fit0.coef().values; V = R @ fit0._vcov @ R.T
wald = float(b @ np.linalg.solve(V, b))
from scipy import stats
out["pretrend_y15_2010_2013"] = {"wald": round(wald, 2), "df": len(pre),
                                 "p": round(float(1 - stats.chi2.cdf(wald, len(pre))), 3)}
del fit0; gc.collect()

# 2. Fixed effects / weights / clustering variants
_, out["year_fe_only"] = run(df, fe="cell_id + year")
_, out["unweighted"] = run(df, weights=None)
_, out["cluster_csa"] = run(df, vcov={"CRV1": "csa"})
_, out["no_controls"] = run(df, controls=())
# strictest: every inventory site type x year (absorbs block-type trends, e.g.
# demolition-heavy rowhouse blocks where unplantable sites cluster)
_, out["all_site_types_x_year"] = run(df, controls=("vac", "mat", "stump", "vacns", "vacpot", "dead"))

# 3. Drop Landsat 7 scenes? The panel is aggregated by year, so instead drop
#    cell-years built from fewer than 3 clear scenes (noisier years).
_, out["min_3_scenes"] = run(df[df.n_scenes >= 3])

# 4. Street-only cells (no park trees) and cells with at least one street site
_, out["no_park_cells"] = run(df[df.park == 0])

# 5. Placebo: "Vacant Site Not Suitable" (spots foresters judged unplantable)
#    should show no systematic cooling.
_, r = run(df, treat=("vacns",), controls=("y15", "y30", "t36", "vac", "mat", "stump"))
out["placebo_not_suitable"] = r["vacns"]

# 6. Binary design: cells with >=1 young tree vs cells with vacant sites only
d = df.copy()
d["young_any"] = (d.young > 0).astype(int)
binary = d[(d.young > 0) | ((d.vac > 0) & (d.young == 0))]
binary = binary.assign(young_any_c=binary.young_any)
fitb = pf.feols("lst_anom ~ i(ybin, young_any_c, ref='base') + i(ybin, mat_c, ref='base') + i(ybin, t36_c, ref='base') | cell_id + nb_year",
                data=binary, weights="n_scenes", vcov={"CRV1": "neighborhood"})
out["binary_young_vs_vacant"] = late_effect(fitb, "young_any")
out["binary_young_vs_vacant"]["n_cells_treated"] = int(binary[binary.young_any == 1].cell_id.nunique())
out["binary_young_vs_vacant"]["n_cells_control"] = int(binary[binary.young_any == 0].cell_id.nunique())
tb = fitb.tidy().reset_index()
tb = tb[tb.Coefficient.str.contains("young_any")]
tb["year"] = tb.Coefficient.str.extract(r"(\d{4})").astype(int)
tb[["year", "Estimate", "Std. Error", "2.5%", "97.5%"]].to_csv(TAB / "event_study_binary.csv", index=False)
del fitb; gc.collect()

# 7. Long difference + sensitivity to unobserved confounding (Cinelli & Hazlett 2020)
w = df.pivot_table(index="cell_id", columns="ybin", values="lst_anom", aggfunc="mean")
late = df[df.year.isin(LATE)].groupby("cell_id").lst_anom.mean()
ld = pd.DataFrame({"dlst": late - w["base"]}).dropna()
cc = df.drop_duplicates("cell_id").set_index("cell_id")
ld = ld.join(cc[["y15_c", "y30_c", "t36_c", "mat_c", "vac_c", "stump_c", "neighborhood"]])
ols = smf.ols("dlst ~ y15_c + y30_c + t36_c + mat_c + vac_c + stump_c + C(neighborhood)", data=ld).fit()
from sensitivity import partial_r2, robustness_value, benchmark_bounds
dof = int(ols.df_resid); t = float(ols.tvalues["y15_c"])
# partial R2 of the benchmark (mature trees) with treatment and with outcome
aux = smf.ols("y15_c ~ y30_c + t36_c + mat_c + vac_c + stump_c + C(neighborhood)", data=ld).fit()
r2dxj = partial_r2(float(aux.tvalues["mat_c"]), int(aux.df_resid))
r2yxj = partial_r2(float(ols.tvalues["mat_c"]), dof)
bnds = benchmark_bounds(float(ols.params["y15_c"]), float(ols.bse["y15_c"]), dof, r2dxj, r2yxj)
out["long_difference_y15"] = {
    "b": round(float(ols.params["y15_c"]), 4), "se": round(float(ols.bse["y15_c"]), 4),
    "p": round(float(ols.pvalues["y15_c"]), 4), "n_cells": int(ols.nobs), "dof": dof,
    "partial_r2_treat": round(partial_r2(t, dof), 5),
    "robustness_value_q1": round(robustness_value(t, dof), 4),
    "robustness_value_q1_alpha05": round(robustness_value(t, dof, alpha=0.05), 4),
    "benchmark": "mature street trees (>6 in) per cell",
    "bounds": [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()} for r in bnds],
}
pd.DataFrame(bnds).to_csv(TAB / "sensitivity_bounds_y15.csv", index=False)

json.dump(out, open(TAB / "robustness.json", "w"), indent=1)
rows = []
for k, v in out.items():
    if isinstance(v, dict) and "y15" in v:
        rows.append({"check": k, **{f"{c}": f"{v[c]['b']:+.3f} [{v[c]['lo']:+.3f}, {v[c]['hi']:+.3f}]" for c in ("y15", "y30", "t36")}})
pd.DataFrame(rows).to_csv(TAB / "robustness_table.csv", index=False)
print(pd.DataFrame(rows).to_string(index=False))
for k in ("pretrend_y15_2010_2013", "placebo_not_suitable", "binary_young_vs_vacant", "long_difference_y15"):
    print(k, json.dumps(out[k])[:700])
