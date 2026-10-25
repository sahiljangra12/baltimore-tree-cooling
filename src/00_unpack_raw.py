"""Unpack the browser extraction (data/raw/extraction_packed.txt) into data/raw/ CSVs.

Format: '|'-separated parts 'name:<base64 gzip>' — meta (JSON), cells (int32
[cell, 13 cols]), anom (int16 [cell, year], °C x anom_scale, -32768 = missing),
n (uint8 clear scenes [cell, year]), csa (GeoJSON), scenes (CSV).
SHA-256 of the packed text: d79fc2ce2fb66ca3ae03093507041b17d91ea81ff214f9f4221aff548ba71686
"""
import base64, gzip, hashlib, json
import numpy as np
import pandas as pd
from common import RAW

blob = (RAW / "extraction_packed.txt").read_text().strip()
assert hashlib.sha256(blob.encode()).hexdigest() == "d79fc2ce2fb66ca3ae03093507041b17d91ea81ff214f9f4221aff548ba71686", "checksum mismatch"
P = dict(p.split(":", 1) for p in blob.split("|"))
dec = lambda k: gzip.decompress(base64.b64decode(P[k]))
meta = json.loads(dec("meta")); NC, NY = meta["NC"], meta["NY"]
C = np.frombuffer(dec("cells"), dtype="<i4").reshape(NC, len(meta["cell_cols"]))
A = np.frombuffer(dec("anom"), dtype="<i2").reshape(NC, NY)
N = np.frombuffer(dec("n"), dtype="u1").reshape(NC, NY)
cells = pd.DataFrame(C, columns=meta["cell_cols"]); cells.insert(0, "cell_id", range(NC))
cells["neighborhood"] = [meta["neighborhoods"][i] for i in cells.nb]; cells = cells.drop(columns="nb")
cells["x"] = cells.cx * 90 + 45; cells["y"] = cells.cy * 90 + 45
cells.to_csv(RAW / "cells_inventory.csv", index=False)
yy = np.array(meta["years"]); ci, yi = np.nonzero(N > 0)
pd.DataFrame({"cell_id": ci, "year": yy[yi], "lst_anom": A[ci, yi] / meta["anom_scale"], "n_scenes": N[ci, yi]}).to_csv(
    RAW / "panel_cell_year_lst.csv", index=False)
(RAW / "csa_plantings_2013_2020.geojson").write_bytes(dec("csa"))
(RAW / "landsat_scenes.csv").write_bytes(dec("scenes"))
print(f"unpacked {NC:,} cells x {NY} years")
