// 01_extract_in_browser.js — the extraction step exactly as it was run (24 Oct 2026).
//
// WHY A BROWSER SCRIPT: the analysis machines could not reach the Planetary Computer
// or Baltimore's GIS server, so the raw data were read in a browser tab opened at
// https://planetarycomputer.microsoft.com/api/stac/v1 and reduced there. Paste the
// three blocks below into that tab's developer console, in order. The result,
// `window._blob`, is the packed file that 00_unpack_raw.py turns into data/raw/.
//
// Sources
//   Trees:   https://baltegis.baltimorecity.gov/mapping/rest/services/Forestry/Trees/MapServer/0
//            (Baltimore Forestry street & park tree inventory, 193,009 records, 2017-18 survey)
//   Landsat: Microsoft Planetary Computer, collection landsat-c2-l2, WRS-2 path 15 row 33,
//            Jun-Aug 2006-2025, eo:cloud_cover < 60 (Landsat 5, 7, 8, 9), surface temperature
//            (lwir / lwir11) and qa_pixel, read as cloud-optimized GeoTIFFs with geotiff.js.
//   CSAs:    https://services1.arcgis.com/mVFRs7NF4iFitgbY/arcgis/rest/services/Treeplnt/FeatureServer/0
//            (BNIA: TreeBaltimore trees planted per Community Statistical Area, 2013-2020)

// ---- Block 1: scene list, SAS token, geotiff.js -------------------------------
const body = {collections: ['landsat-c2-l2'], bbox: [-76.712, 39.197, -76.529, 39.372],
  datetime: '2003-06-01/2025-08-31',
  query: {'eo:cloud_cover': {lt: 60}, 'landsat:wrs_path': {eq: '015'}, 'landsat:wrs_row': {eq: '033'}}, limit: 500};
const r = await fetch('/api/stac/v1/search', {method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify(body)}).then(r => r.json());
window._items = r.features.filter(f => { const m = +f.properties.datetime.slice(5, 7); return m >= 6 && m <= 8; });
window.GeoTIFF = await import('https://cdn.jsdelivr.net/npm/geotiff@2.1.3/+esm');
window._tok = (await fetch('/api/sas/v1/token/landsat-c2-l2').then(r => r.json())).token;
// note: the first 500 results (newest first) reach back to 2006; 2003-05 were not used.

// ---- Block 2: tree inventory (all records, UTM 18N coordinates) ----------------
{
const base = 'https://baltegis.baltimorecity.gov/mapping/rest/services/Forestry/Trees/MapServer/0/query';
const ids = await fetch(`${base}?where=1%3D1&returnIdsOnly=true&f=json`).then(r => r.json());
const all = ids.objectIds.sort((a, b) => a - b); const chunks = [];
for (let i = 0; i < all.length; i += 1000) chunks.push(all.slice(i, i + 1000));
const recs = [];
const run = async c => { for (let k = 0; k < 3; k++) { try {
  const r = await fetch(base, {method: 'POST', headers: {'content-type': 'application/x-www-form-urlencoded'},
    body: new URLSearchParams({objectIds: c.join(','), outFields: 'OBJECTID,SPP,COMMON,DBH,CONDITION,LOC_TYPE,SPACE_TYPE,Neighborhood,Inv_Date,MT',
      outSR: '32618', returnGeometry: 'true', f: 'json'})}).then(r => r.json());
  for (const f of r.features) { const a = f.attributes;
    recs.push([a.OBJECTID, a.SPP, a.COMMON, a.DBH, a.CONDITION, a.LOC_TYPE, a.SPACE_TYPE, a.Neighborhood, a.Inv_Date, a.MT,
      f.geometry ? f.geometry.x : null, f.geometry ? f.geometry.y : null]); }
  return; } catch (e) {} } };
for (let i = 0; i < chunks.length; i += 8) await Promise.all(chunks.slice(i, i + 8).map(run));
window._trees = recs;
}

// ---- Block 3: per-scene LST -> 90 m cell anomalies -----------------------------
// For each scene: LST = ST*0.00341802 + 149 - 273.15 (°C); drop fill, dilated cloud,
// cirrus, cloud, shadow, snow, water (QA bits 1,2,3,4,5,7); keep scenes with >=30% of
// the city box clear; drop residual cloud pixels below max(15 °C, scene median - 15);
// anomaly = pixel - scene median; average pixels into 90 m cells (>=4 of 9 valid);
// then average each cell's scene anomalies within a year.
{
const G = window.GeoTIFF, T = window._trees, I = window._items.slice().sort((a, b) => a.properties.datetime.localeCompare(b.properties.datetime));
const CELL = 90; const cells = new Map(); let xmin = 1e12, xmax = -1e12, ymin = 1e12, ymax = -1e12;
const VAC = new Set(['Vacant Site', 'Vacant Potential', 'Vacant Site Not Suitable', 'Stump']);
for (const r of T) { const [id, spp, common, dbh, cond, loc, space, nb, inv, mt, x, y] = r; if (x == null) continue;
  xmin = Math.min(xmin, x); xmax = Math.max(xmax, x); ymin = Math.min(ymin, y); ymax = Math.max(ymax, y);
  const cx = Math.floor(x / CELL), cy = Math.floor(y / CELL), k = cx + '_' + cy;
  let c = cells.get(k); if (!c) { c = {cx, cy, nb: {}, y15: 0, y30: 0, t36: 0, mat: 0, vac: 0, vacpot: 0, vacns: 0, stump: 0, dead: 0, park: 0}; cells.set(k, c); }
  c.nb[nb] = (c.nb[nb] || 0) + 1;
  const isLive = !VAC.has(spp) && cond !== 'Absent' && cond !== 'Stump' && cond !== 'Dead';
  if (loc === 'Park') { if (isLive) c.park++; continue; }
  if (spp === 'Vacant Site') c.vac++; else if (spp === 'Vacant Potential') c.vacpot++; else if (spp === 'Vacant Site Not Suitable') c.vacns++;
  else if (spp === 'Stump' || cond === 'Stump') c.stump++; else if (cond === 'Dead') c.dead++;
  else if (isLive) { if (dbh <= 1.5) c.y15++; else if (dbh <= 3) c.y30++; else if (dbh <= 6) c.t36++; else c.mat++; } }
const keys = [...cells.keys()]; const idx = new Map(keys.map((k, i) => [k, i]));
const bbox = [xmin - 300, ymin - 300, xmax + 300, ymax + 300];
const years = []; for (let y = 2006; y <= 2025; y++) years.push(y);
const NC = keys.length, NY = years.length, S = new Float64Array(NC * NY), N = new Uint16Array(NC * NY), sceneLog = [];
window._job = {cells, keys, bbox, years, S, N, sceneLog, done: 0, total: I.length, errors: [], status: 'running'};
const REJ = (1 << 1) | (1 << 2) | (1 << 3) | (1 << 4) | (1 << 5) | (1 << 7);
async function proc(it) {
  const stA = it.assets.lwir11 || it.assets.lwir;
  const [a, b] = await Promise.all([G.fromUrl(stA.href + '?' + window._tok), G.fromUrl(it.assets.qa_pixel.href + '?' + window._tok)]);
  const [ia, ib] = await Promise.all([a.getImage(), b.getImage()]);
  const [ox, oy] = ia.getOrigin(); const W = ia.getWidth(), H = ia.getHeight();
  const c0 = Math.max(0, Math.floor((bbox[0] - ox) / 30)), c1 = Math.min(W, Math.ceil((bbox[2] - ox) / 30));
  const r0 = Math.max(0, Math.floor((oy - bbox[3]) / 30)), r1 = Math.min(H, Math.ceil((oy - bbox[1]) / 30));
  const win = [c0, r0, c1, r1];
  const [st, qa] = await Promise.all([ia.readRasters({window: win, samples: [0]}), ib.readRasters({window: win, samples: [0]})]);
  const A = st[0], Q = qa[0], w = c1 - c0, h = r1 - r0, n = w * h; const L = new Float32Array(n); let valid = 0; const vals = [];
  for (let i = 0; i < n; i++) { const s = A[i], q = Q[i]; if (s > 0 && q !== 1 && (q & REJ) === 0) { const t = s * 0.00341802 + 149 - 273.15; L[i] = t; vals.push(t); valid++; } else L[i] = NaN; }
  const frac = valid / n; let med = NaN, used = false, kept = 0;
  if (valid > 1000) { vals.sort((p, q) => p - q); med = vals[vals.length >> 1]; }
  const yi = years.indexOf(+it.properties.datetime.slice(0, 4));
  if (frac >= 0.30 && yi >= 0 && isFinite(med)) { used = true; const lo = Math.max(15, med - 15); const cs = new Map();
    for (let r = 0; r < h; r++) { const cy = Math.floor((oy - 30 * (r0 + r + 0.5)) / CELL);
      for (let c = 0; c < w; c++) { const t = L[r * w + c]; if (!(t >= lo)) continue;
        const j = idx.get(Math.floor((ox + 30 * (c0 + c + 0.5)) / CELL) + '_' + cy); if (j === undefined) continue;
        let e = cs.get(j); if (!e) { e = [0, 0]; cs.set(j, e); } e[0] += t - med; e[1]++; } }
    for (const [j, e] of cs) { if (e[1] >= 4) { S[j * NY + yi] += e[0] / e[1]; N[j * NY + yi]++; kept++; } } }
  sceneLog.push({id: it.id, date: it.properties.datetime.slice(0, 10), platform: it.properties.platform, cloud: it.properties['eo:cloud_cover'],
    clear_frac: +frac.toFixed(3), median_lst: isFinite(med) ? +med.toFixed(2) : null, used, cells: kept});
}
let k = 0; const worker = async () => { while (k < I.length) { const it = I[k++];
  for (let t = 0; t < 3; t++) { try { await proc(it); break; } catch (e) { if (t === 2) window._job.errors.push(it.id + ': ' + e); else await new Promise(r => setTimeout(r, 2000)); } }
  window._job.done++; } };
await Promise.all(Array.from({length: 4}, worker)); window._job.status = 'done';
}
// Packing (cells int32, anomalies int16 at 0.01 °C, scene counts uint8, gzip+base64)
// is in the session notes; 00_unpack_raw.py documents the format it reads.
