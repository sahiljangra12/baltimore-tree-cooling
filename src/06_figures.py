"""Paper figures (PDF + PNG, 300 dpi)."""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from common import TAB, FIG, COHORTS

INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
SERIES = {"y15": "#2a78d6", "y30": "#eb6834", "t36": "#1baf7a"}   # reference categorical slots 1-3
WINDOW = {"y15": (2014, 2017), "y30": (2010, 2015), "t36": (2006, 2011)}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK2,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "figure.facecolor": SURF, "axes.facecolor": SURF})

def style(ax):
    ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.axhline(0, color=INK2, lw=0.9)

def save(fig, name):
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight"); fig.savefig(FIG / f"{name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

# Figure 1: event study by trunk-size cohort
es = pd.read_csv(TAB / "event_study_main.csv")
fig, axes = plt.subplots(1, 3, figsize=(10, 3.4), sharey=True)
for ax, k in zip(axes, ["y15", "y30", "t36"]):
    d = es[es.cohort == k]
    style(ax)
    ax.axvspan(*WINDOW[k], color=SERIES[k], alpha=0.08, lw=0)
    ax.text(sum(WINDOW[k]) / 2, 0.033, "implied\nplanting", ha="center", va="top", fontsize=7.5, color=INK2)
    ax.axvspan(2005.5, 2009.5, color=GRID, alpha=0.5, lw=0)
    ax.text(2007.5, -0.071, "reference\n2006–09", ha="center", va="bottom", fontsize=7.5, color=INK2)
    ax.vlines(d.year, d.lo, d.hi, color=SERIES[k], lw=1.6)
    ax.plot(d.year, d.b, "o", ms=4.5, color=SERIES[k], mec=SURF, mew=1)
    ax.set_title(COHORTS[k], fontsize=9, color=INK, loc="left")
    ax.set_xticks([2006, 2010, 2014, 2018, 2022]); ax.set_xlim(2005.3, 2025.7)
axes[0].set_ylabel("Change in cell surface temperature\nper street tree (°C, 95% CI)")
axes[0].set_ylim(-0.075, 0.04)
fig.suptitle("Young street trees cool their 90 m surroundings as they grow; no change before planting",
             x=0.01, ha="left", fontsize=10.5, color=INK, fontweight="bold", y=1.04)
save(fig, "fig1_event_study_cohorts")

# Figure 2: the naive neighborhood design fails its pre-trend test; the block design passes
csa = pd.read_csv(TAB / "csa_event_study.csv")
y15 = es[es.cohort == "y15"]
fig, axes = plt.subplots(1, 2, figsize=(9, 3.3))
for ax, d, col, ttl, yl, lo, hi, pre in [
    (axes[0], csa.rename(columns={"Estimate": "b", "2.5%": "lo", "97.5%": "hi"}), INK2,
     "A. Neighborhood design (55 CSAs)", "°C per 100 trees planted per km²", "lo", "hi", (2009, 2012)),
    (axes[1], y15, SERIES["y15"], "B. Block design, neighborhood × year FE", "°C per young tree (≤1.5 in)", "lo", "hi", (2010, 2013))]:
    style(ax)
    ax.axvspan(pre[0] - 0.5, pre[1] + 0.5, color="#e34948", alpha=0.07, lw=0)
    ax.text(sum(pre) / 2, 0.97, "pre-period", ha="center", va="top", fontsize=7.5, color=INK2, transform=ax.get_xaxis_transform())
    ax.vlines(d.year, d[lo], d[hi], color=col, lw=1.6)
    ax.plot(d.year, d.b, "o", ms=4.5, color=col, mec=SURF, mew=1)
    ax.set_title(ttl, fontsize=9, color=INK, loc="left"); ax.set_ylabel(yl)
    ax.set_xticks([2009, 2013, 2017, 2021, 2025]); ax.set_xlim(2008.3, 2025.7)
r = json.load(open(TAB / "robustness.json")); c = json.load(open(TAB / "csa_pilot.json"))
axes[0].text(0.98, 0.97, f"pre-trend p < 0.001", transform=axes[0].transAxes, ha="right", va="top", fontsize=8, color=INK)
axes[1].text(0.98, 0.97, f"pre-trend p = {r['pretrend_y15_2010_2013']['p']:.2f}", transform=axes[1].transAxes, ha="right", va="top", fontsize=8, color=INK)
fig.suptitle("Comparing whole neighborhoods picks up pre-existing cooling; comparing blocks within a neighborhood does not",
             x=0.01, ha="left", fontsize=10.5, color=INK, fontweight="bold", y=1.04)
fig.subplots_adjust(wspace=0.3)
save(fig, "fig2_design_comparison")
print("figures written")
