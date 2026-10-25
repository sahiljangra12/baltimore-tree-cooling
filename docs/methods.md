# Methods and audit trail

Every number below is produced by the scripts in `src/` and stored in `outputs/results.json` or `outputs/tables/`.

## 1. Data

**Street-tree inventory.** Baltimore City Recreation & Parks, Forestry Division, map service `Forestry/Trees/MapServer/0` on `baltegis.baltimorecity.gov`, read 24 Oct 2026: 193,009 records. Fields used are species, trunk diameter (DBH, inches), condition, location type (street/park), neighborhood and point location. Nearly all records were created in the 2017–18 field census (105,168 in 2017, 87,044 in 2018). Fewer than 700 were added or edited later. `PLANTED_SEASON` is filled for about 220 records and `PLANTINGSTATUS` for none, so the public layer cannot date plantings directly.

Record types per 90 m cell (street records only, unless noted):

| Variable | Definition | Total |
|---|---|---|
| `y15` | live tree, DBH ≤ 1.5 in | 5,959 |
| `y30` | live tree, 1.5 < DBH ≤ 3 in | 12,612 |
| `t36` | live tree, 3 < DBH ≤ 6 in | 15,299 |
| `mat` | live tree, DBH > 6 in | 50,542 |
| `vac` | "Vacant Site" (empty site the city considers plantable) | 44,469 |
| `vacpot`, `vacns` | "Vacant Potential", "Vacant Site Not Suitable" | see `cells_inventory.csv` |
| `stump`, `dead`, `park` | stumps, dead trees, live park trees | see `cells_inventory.csv` |

**Landsat surface temperature.** Collection 2 Level-2 surface temperature from the Microsoft Planetary Computer, WRS-2 path 15 / row 33, June–August, scene cloud cover < 60%, 2006–2025 (Landsat 5, 7, 8, 9). There were 151 scenes. 111 passed the clear-sky rule and one failed to read. Per scene:

- LST (°C) = ST × 0.00341802 + 149 − 273.15.
- Mask fill and QA_PIXEL bits 1–5 and 7 (dilated cloud, cirrus, cloud, shadow, snow, water).
- Keep the scene if ≥ 30% of the city box is clear.
- Drop residual-cloud pixels colder than max(15 °C, scene median − 15 °C). This is the same rule as the Baltimore Heat Atlas.
- Anomaly = pixel minus the scene's city-box median. This removes weather and sensor differences between days.
- Average the 30 m pixels into 90 m cells (≥ 4 of 9 valid), then average each cell's scene anomalies within the year.

Landsat thermal bands are natively 60–120 m and resampled to 30 m, so 90 m is close to the true thermal resolution.

**Neighborhood planting counts.** BNIA indicator "Number of Trees Planted", TreeBaltimore, by Community Statistical Area (55 CSAs), 2013–2020: 30,792 trees in total.

## 2. Identification

**Timing from trunk size (assumption).** Street trees are planted as roughly 1.5–2 in caliper nursery stock and add roughly 0.25–0.5 in of diameter per year when young. A tree at ≤ 1.5 in in 2017–18 was therefore planted within a few years before the survey, about 2014–17. A tree at 1.5–3 in was planted about 2010–15, and one at 3–6 in about 2003–11. These windows are approximate. The design tests them: each cohort's cooling should start after its window, not before.

**Comparison group.** Every cell is compared with other cells in the same neighborhood and year (neighborhood × year fixed effects). Each site type × year is controlled, including empty plantable sites.

**Model.**

LST_anom[i,t] = α_i + δ_{neighborhood,t} + Σ_t Σ_k β_{k,t} · Count_{k,i} · 1[year = t] + Σ_t Σ_c γ_{c,t} · Control_{c,i} · 1[year = t] + ε

The reference period is 2006–09 pooled. Counts are capped at 10 per cell (about the 99th percentile). Weights are the number of clear scenes in the cell-year. Standard errors are clustered by neighborhood (277 clusters). Estimation uses `pyfixest`.

## 3. Results

| 2022–25 vs 2006–09, °C per tree | Estimate | 95% CI |
|---|---|---|
| DBH ≤ 1.5 in | −0.026 | −0.047, −0.005 |
| DBH 1.5–3 in | −0.015 | −0.031, 0.000 |
| DBH 3–6 in | −0.029 | −0.046, −0.012 |
| Vacant plantable site | +0.013 | +0.001, +0.024 |

- ≤ 1.5 in: coefficients are flat through 2017. Cooling appears from 2018 and grows to −0.035 °C in 2025. The pre-trend joint test for 2010–13 gives χ² = 2.59, 4 df, p = 0.63.
- 3–6 in: cooling builds from about 2016. That fits trees planted 2003–11 whose crowns began to matter in the mid-2010s.
- 1.5–3 in: smaller effect, and a small dip in 2010–12 that does not fit cleanly. This is reported as is.
- Vacant plantable sites warm slightly over time. That is consistent with some of them being trees lost between 2006 and the 2017 survey.

**Binary version.** Cells with ≥ 1 young tree (4,741) are compared with cells that have vacant sites but no young trees (6,064). The 2022–25 effect is −0.089 °C per cell (95% CI −0.159, −0.019).

**Sensitivity (Cinelli & Hazlett 2020)** uses a long difference: (2022–25 mean) − (2006–09 mean) per cell, on counts, controls and neighborhood fixed effects.

- Estimate per young tree: −0.028 (SE 0.007).
- Robustness value 3.1% (1.5% at α = 0.05).
- A confounder 1×, 2× or 3× as strong as mature-tree density would move the estimate only to −0.026, −0.025 or −0.024. All of these intervals exclude zero.

## 4. Checks that failed or are weak

- **Placebo on "not suitable" sites fails** (−0.088 °C per site, CI −0.115, −0.062). These sites concentrate in dense rowhouse neighborhoods with heavy vacancy and demolition (Harlem Park, Sandtown-Winchester, Upton, Broadway East, Oliver), and their cooling begins around 2010. That points to block-level change, such as demolitions turning roofs into lots, rather than trees. Controlling all site types × year leaves the young-tree estimate at −0.027 (CI −0.048, −0.006). The fix is to add the city's demolition records as a direct control.
- **Neighborhood design (55 CSAs) fails its pre-trend test** (2009–12 coefficients jointly χ² = 86, p < 0.001). Neighborhoods that later received more trees were already cooling. This is why the block design is the main analysis.
- **Year fixed effects only** (no neighborhood × year) inflates the effect 3–4×. Neighborhood-wide trends are large, and the main specification removes them.

## 5. Next steps

1. Request planting work orders with dates (Cityworks) from the Forestry Division. This would replace trunk-size cohorts with exact staggered timing (Callaway & Sant'Anna estimator).
2. Add demolition permits and vacant-building notices as time-varying controls.
3. Heterogeneity by HOLC grade and by baseline canopy.
4. Air temperature: test against the 2018 Baltimore heat-mapping campaign or a sensor network, since surface temperature overstates what people feel.
