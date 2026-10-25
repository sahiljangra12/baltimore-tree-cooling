"""Omitted-variable-bias sensitivity (Cinelli & Hazlett 2020, JRSS-B), closed form.

Implemented directly because the PySensemakr release fails with recent pandas.
Formulas follow Cinelli & Hazlett (2020), Sections 4-6.
"""
import numpy as np
from scipy import stats

def partial_r2(t, dof):
    return t**2 / (t**2 + dof)

def robustness_value(t, dof, q=1.0, alpha=None):
    f = q * abs(t) / np.sqrt(dof)
    if alpha is not None:
        fcrit = stats.t.ppf(1 - alpha / 2, dof - 1) / np.sqrt(dof - 1)
        f = f - fcrit
        if f <= 0:
            return 0.0
    return 0.5 * (np.sqrt(f**4 + 4 * f**2) - f**2)

def benchmark_bounds(b, se, dof, r2dxj_x, r2yxj_dx, kd=(1, 2, 3), ky=None, alpha=0.05):
    """Bounds on a confounder kd (ky) times as strong as observed covariate X_j.
    r2dxj_x: partial R2 of X_j with the treatment (given other covariates)
    r2yxj_dx: partial R2 of X_j with the outcome (given treatment and others)"""
    rows = []
    for k in kd:
        kyk = k if ky is None else ky
        r2dz_x = k * r2dxj_x / (1 - r2dxj_x)
        if r2dz_x >= 1:
            rows.append({"kd": k, "r2dz_x": None}); continue
        r2zxj = k * r2dxj_x**2 / ((1 - k * r2dxj_x) * (1 - r2dxj_x))
        r2yz_dx = min(1.0, ((np.sqrt(kyk) + np.sqrt(r2zxj)) / np.sqrt(1 - r2zxj))**2 * r2yxj_dx / (1 - r2yxj_dx))
        bias = se * np.sqrt(dof) * np.sqrt(r2yz_dx * r2dz_x / (1 - r2dz_x))
        adj = np.sign(b) * (abs(b) - bias)
        adj_se = se * np.sqrt((1 - r2yz_dx) / (1 - r2dz_x)) * np.sqrt(dof / (dof - 1))
        tcrit = stats.t.ppf(1 - alpha / 2, dof - 1)
        rows.append({"kd": k, "ky": kyk, "r2dz_x": r2dz_x, "r2yz_dx": r2yz_dx,
                     "adjusted_estimate": adj, "adjusted_lo": adj - tcrit * adj_se,
                     "adjusted_hi": adj + tcrit * adj_se})
    return rows
