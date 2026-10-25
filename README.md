# Do new street trees cool Baltimore?

[![reproduce](https://github.com/sahiljangra12/baltimore-tree-cooling/actions/workflows/reproduce.yml/badge.svg)](https://github.com/sahiljangra12/baltimore-tree-cooling/actions/workflows/reproduce.yml)

**A within-neighborhood event study of Baltimore's street-tree plantings and summer surface temperature, 2006–2025.**
Sahil, Johns Hopkins University. Working draft, October 2026.

## Headline result

Each young street tree (trunk ≤ 1.5 in in the 2017–18 city inventory, so planted roughly 2014–17) lowered the summer surface temperature of its 90 m surroundings by **0.026 °C by 2022–25** relative to 2006–09 (95% CI 0.005–0.047 °C), with **no change before planting** (pre-trend test p = 0.63). The cooling appears only after 2018 and grows as the trees mature. A block with five new saplings is about 0.13 °C cooler.

That size is what simple physics predicts: a young crown shades roughly 0.2% of a 90 m cell, and shade is 10–15 °C cooler than sunlit pavement, giving 0.02–0.03 °C per tree.

The naive comparison of whole neighborhoods fails: neighborhoods that later got more trees were already cooling in 2009–12 (pre-trend p < 0.001), the selection problem this design exists to solve. See `outputs/figures/fig2_design_comparison.png`.

## Design in one paragraph

Baltimore's Forestry Division surveyed every public street tree and every empty planting site in 2017–18 (193,009 records). Trunk size dates the young trees. Empty sites the city judged plantable are the comparison group: same streetscape screen, no tree yet. Landsat 5/7/8/9 summer scenes (111 usable, 2006–2025) give each 90 m cell's surface temperature relative to that day's citywide median. The regression has cell fixed effects and neighborhood × year fixed effects, so it compares blocks within the same neighborhood in the same year. It interacts the count of trees in each trunk-size cohort with year, controlling for vacant sites, mature trees and stumps × year. Standard errors are clustered by neighborhood (277).

## What is in this folder

| Path | Contents |
|---|---|
| `src/01_extract_in_browser.js` | The raw-data extraction exactly as run (inventory + Landsat + CSA counts), in a browser tab on the Planetary Computer |
| `src/00_unpack_raw.py` | Unpacks `data/raw/extraction_packed.txt` (checksum-verified) into the raw CSVs |
| `src/02_build_panel.py` | Cell × year analysis panel |
| `src/03_event_study.py` | Main event study by trunk-size cohort |
| `src/04_robustness.py` | Pre-trend test, FE/weight/cluster variants, strictest controls, placebo, binary design, long difference + sensitivity |
| `src/sensitivity.py` | Cinelli & Hazlett (2020) omitted-variable-bias bounds |
| `src/05_csa_pilot.py` | Neighborhood-level (55 CSAs) pilot using TreeBaltimore planting counts |
| `src/06_figures.py`, `src/07_summary.py` | Figures and `outputs/results.json` |
| `outputs/tables/` | All estimates as CSV/JSON |
| `outputs/figures/` | Figures (PDF + 300 dpi PNG) |
| `docs/methods.md` | Data, assumptions, every check and its result, limitations |
| `docs/DATA_PROVENANCE.md` | Sources, exact queries, access date, checksums |
| `docs/VERIFICATION.md` | Latest verification report (generated) |
| `src/08_tex.py`, `src/09_verify.py` | Paper numbers from outputs; reproducibility checks |
| `paper/` | LaTeX working paper `Baltimore_Street_Trees_Cooling_Sahil_2026.pdf`; rebuild with `bash paper/build.sh` (numbers come from `outputs/` via `src/08_tex.py`) |

## Run it

```bash
pip install -r requirements-lock.txt   # exact versions used for the committed results
bash run_all.sh                         # under a minute; regenerates every table and figure
python3 src/09_verify.py                # 25 checks; writes docs/VERIFICATION.md
bash paper/build.sh                     # optional: rebuild the PDF (needs LaTeX)
```

## Proof of reproducibility

- **Raw data are fixed and checksummed.** `data/raw/extraction_packed.txt` carries a SHA-256 recorded at extraction (`d79fc2ce…`); the unpacking step refuses to run if it differs. Where each byte came from is in [`docs/DATA_PROVENANCE.md`](docs/DATA_PROVENANCE.md), and the extraction code is committed verbatim (`src/01_extract_in_browser.js`).
- **Every quoted number is checked.** `src/09_verify.py` recomputes the headline estimates from `outputs/` and confirms the README, methods note and paper quote exactly those values. The paper never contains a typed number: all of them come from `paper/macros.tex`, written by `src/08_tex.py`.
- **Clean-machine rebuild on every push.** The `reproduce` GitHub Actions workflow installs the locked environment on a fresh Ubuntu runner, rebuilds everything from the packed data and runs the checks. The badge above shows the latest result, and each run uploads its `VERIFICATION.md`.
- **Current report:** [`docs/VERIFICATION.md`](docs/VERIFICATION.md), with environment versions and a SHA-256 manifest of every output.

## Robustness (2022–25 effect per young tree, °C, 95% CI)

| Check | Estimate |
|---|---|
| Main specification | −0.026 [−0.047, −0.005] |
| All site types × year (strictest) | −0.027 [−0.048, −0.006] |
| Unweighted | −0.028 [−0.048, −0.007] |
| Clustered by 55 CSAs | −0.026 [−0.047, −0.006] |
| Cell-years with ≥ 3 clear scenes | −0.026 [−0.047, −0.005] |
| Excluding cells with park trees | −0.023 [−0.045, −0.002] |
| Year FE only (no neighborhood × year) | −0.096 [−0.131, −0.060] |
| Long difference, sensitivity-adjusted for a confounder 3× as strong as mature-tree density | −0.024 [−0.038, −0.009] (unadjusted long difference −0.028) |

The year-FE-only estimate is 3–4 times larger, which shows how much neighborhood-wide trends would inflate a naive estimate.

## Known problems (read before citing)

1. **Planting dates are inferred from trunk size.** The city's public layer has no usable planting date (`PLANTED_SEASON` is filled for about 220 of 193,009 records). Exact dates would sharpen the design; ask the Forestry Division for Cityworks planting work orders.
2. **The placebo failed.** "Not suitable" planting sites also cool (−0.09 °C per site). They cluster in dense rowhouse blocks (Harlem Park, Sandtown-Winchester, Upton, Broadway East) that have cooled since 2010, plausibly from vacant-house demolitions. The young-tree estimate does not move when those trends are controlled, but demolition data should be added directly.
3. **Surface temperature, not air temperature or health.** Landsat measures surface (skin) temperature on clear summer late mornings, when Landsat passes over.
4. **Survivorship.** Only trees alive in 2017–18 are counted, which biases toward successful plantings.
5. One of 151 Landsat scenes (LC08 2022-08-04) failed to read and is excluded.

## Citation and license

Cite via [`CITATION.cff`](CITATION.cff). Code is MIT-licensed; the paper text and figures are CC BY 4.0; the data derive from public sources listed in the provenance note.
