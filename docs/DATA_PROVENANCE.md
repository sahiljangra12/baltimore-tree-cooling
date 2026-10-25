# Data provenance

Every input is public. All three sources were read on **24 October 2026** in a browser
tab on the Microsoft Planetary Computer, using `src/01_extract_in_browser.js` exactly as
committed. The machines that ran the analysis could not reach these servers directly.
The browser reduced the raw data to one packed text file, `data/raw/extraction_packed.txt`,
which is committed to this repository.

| | |
|---|---|
| Packed file | `data/raw/extraction_packed.txt` (906,774 bytes) |
| SHA-256 | `d79fc2ce2fb66ca3ae03093507041b17d91ea81ff214f9f4221aff548ba71686` |
| Verified | at extraction, after transfer to the analysis machine, and by `src/09_verify.py` on every run |
| Unpacked by | `src/00_unpack_raw.py` (refuses to run if the checksum differs) |

## 1. Baltimore street and park tree inventory

- **Publisher:** Baltimore City Department of Recreation and Parks, Forestry Division
- **Service:** `https://baltegis.baltimorecity.gov/mapping/rest/services/Forestry/Trees/MapServer/0`
  (found through the Open Baltimore "Baltimore Tree Inventory" web app, item `d2cfbbe9a24b4d988de127852e6c26c8`)
- **Query:** all 193,009 object IDs, in batches of 1,000; fields `OBJECTID, SPP, COMMON, DBH, CONDITION,
  LOC_TYPE, SPACE_TYPE, Neighborhood, Inv_Date, MT`; geometry in UTM 18N (EPSG:32618)
- **Facts checked on the live service:** 105,168 records created in 2017 and 87,044 in 2018. `PLANTED_SEASON`
  is filled for about 220 records and `PLANTINGSTATUS` for none, so planting dates are not available publicly.
- **Kept in the packed file:** per-90 m-cell counts by record type (not the individual records)

## 2. Landsat Collection 2 Level-2 surface temperature

- **Publisher:** USGS, served by the Microsoft Planetary Computer, collection `landsat-c2-l2`
- **Search:** WRS-2 path 015, row 033; bounding box −76.712, 39.197, −76.529, 39.372; June–August;
  `eo:cloud_cover < 60`; 2006–2025 (151 scenes: Landsat 5, 7, 8, 9)
- **Assets read:** `lwir11` (Landsat 8/9) or `lwir` (Landsat 5/7), and `qa_pixel`, as cloud-optimized
  GeoTIFFs (geotiff.js 2.1.3), windowed to the city
- **Processing:** see `docs/methods.md` §1. 111 scenes passed the clear-sky rule. One scene
  (`LC08_L2SP_015033_20220804_02_T1`) failed to read and is recorded in `data/raw/landsat_scenes.csv`.
- **Kept in the packed file:** per-cell annual mean temperature relative to the scene's citywide median
  (0.01 °C precision), clear-scene counts, and the per-scene log

## 3. Trees planted by Community Statistical Area

- **Publisher:** Baltimore Neighborhood Indicators Alliance (source: TreeBaltimore)
- **Service:** `https://services1.arcgis.com/mVFRs7NF4iFitgbY/arcgis/rest/services/Treeplnt/FeatureServer/0`
- **Content:** trees planted per CSA, 2013–2020, 55 CSAs, with boundaries (UTM 18N, generalized to 15 m)
- **Kept in the packed file:** the GeoJSON as returned

## What is not here

- Exact planting dates (not public; request Cityworks work orders from the Forestry Division)
- Demolition and lot-greening records (to be added as controls)
- Air temperature or health outcomes
