"""Main result: event study of surface temperature on young street-tree counts.

    LST_anom[i,t] = a_i + d_{nbhd,t} + sum_t b_t^k * Count_i^k * 1[year=t] + controls x year + e

k = trunk-size cohorts (y15, y30, t36). Controls interacted with year: vacant planting
sites, mature trees (>6"), stumps. Reference period = 2006-2009 pooled. Cell fixed
effects; neighborhood x year fixed effects; weights = clear scenes in the cell-year;
SEs clustered by neighborhood. Counts capped at 10 per cell.
"""
import json
import numpy as np
import pandas as pd
import pyfixest as pf
from common import PROC, TAB, COHORTS

df = pd.read_csv(PROC / "analysis_panel.csv")

def es_formula(treat, controls):
    terms = [f"i(ybin, {v}_c, ref='base')" for v in treat + controls]
    return "lst_anom ~ " + " + ".join(terms) + " | cell_id + nb_year"

def tidy_es(fit, var):
    t = fit.tidy().reset_index()
    t = t[t.Coefficient.str.contains(f":{var}_c") | t.Coefficient.str.endswith(f"{var}_c")]
    t = t[t.Coefficient.str.contains("ybin")]
    t["year"] = t.Coefficient.str.extract(r"ybin::(\d{4})").astype(int)
    out = t[["year", "Estimate", "Std. Error", "2.5%", "97.5%"]].rename(
        columns={"Estimate": "b", "Std. Error": "se", "2.5%": "lo", "97.5%": "hi"})
    out.insert(0, "cohort", var)
    return out.sort_values("year")

treat = ["y15", "y30", "t36"]
controls = ["vac", "mat", "stump"]
fit = pf.feols(es_formula(treat, controls), data=df, weights="n_scenes",
               vcov={"CRV1": "neighborhood"})
es = pd.concat([tidy_es(fit, v) for v in treat + ["vac"]])
es.to_csv(TAB / "event_study_main.csv", index=False)

# Pooled pre/post contrasts per cohort (period means of the yearly coefficients)
def pooled(fit, var, years):
    names = [f"C(ybin,contr.treatment(base='base'))[T.{y}]:{var}_c" for y in years]
    coefs = fit.coef(); V = fit._vcov; idx = list(coefs.index)
    names = [n for n in idx if (f":{var}_c" in n or n.endswith(f"{var}_c")) and any(f"{y}" in n for y in years)]
    w = np.zeros(len(idx))
    for n in names: w[idx.index(n)] = 1 / len(names)
    est = float(w @ coefs.values); se = float(np.sqrt(w @ V @ w))
    return {"b": est, "se": se, "lo": est - 1.96 * se, "hi": est + 1.96 * se, "n_years": len(names)}

res = {"n_cells": int(df.cell_id.nunique()), "n_obs": int(fit._N),
       "n_clusters": int(df.neighborhood.nunique()), "r2_within": float(fit._r2_within)}
for v in treat + ["vac"]:
    res[v] = {"2010_2013": pooled(fit, v, range(2010, 2014)),
              "2014_2017": pooled(fit, v, range(2014, 2018)),
              "2018_2021": pooled(fit, v, range(2018, 2022)),
              "2022_2025": pooled(fit, v, range(2022, 2026))}
json.dump(res, open(TAB / "event_study_main.json", "w"), indent=1)
pd.set_option("display.width", 160)
print(es.round(3).to_string(index=False))
print(json.dumps(res, indent=1)[:3000])
