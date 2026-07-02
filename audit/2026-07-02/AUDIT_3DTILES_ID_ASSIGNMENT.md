# Audit: 3D-tile (Cesium/IFC) building-ID assignment

**Date:** 2026-07-02
**Scope:** How a Cesium 3D building mesh's id links back to its CIDOC-CRM building
record; whether that linkage is stable/collision-safe.
**Tool:** `utils/sparql_query.py` / `utils/reconcile_3dtiles.py` against production
Blazegraph (`https://veniss.net/sparql`) and the live `xdtiler3d` manifests. `SELECT`/`ASK`
only — read-only.
**Note:** `https://veniss.net/sparql` sits behind Cloudflare, which returns `HTTP 403
error 1010` for the default Python-urllib User-Agent regardless of valid credentials.
`utils/sparql_query.py` now sends a browser User-Agent to work around this.

## Background: where 3D tiles come from, and where the id originates

3D-tile generation happens **outside this repo**, in an external `metapolis-xdtiler`
service, reached via the `xdtiler3d` reverse proxy (`config/proxy.prop`). This repo only
consumes the result: `data/templates/https%3A%2F%2Fveniss.net%2Fresource%2FMap.html:5`
loads `cesium-asset-urls='https://veniss.net/proxy/xdtiler3d/tiles/ifc/LZV/manifest_compat.json'`.

Only **LZV** (Lazzaretto Vecchio) currently has a published 3D tileset; manifests for
`PVG, SSP, SSC, CRT, SSV, MDM, LZN` all 404.

The manifest keys each building mesh by a `code` (= IFC `root_id`) plus `isl_code`:

```json
"13": {"root_id": "13", "isl_code": "LZV", "path": "ifc/LZV/buildings/13", ...}
```

The 40 LZV codes are **sparse and non-contiguous**
(`1-9, 10, 12, 13, 15-25, 31, 35-38, 43, 52, 57, 74, 77, 87, 88, 91, 97, 98, 99, 101`) —
not `1..40`. This rules out array-index / insertion-order assignment: the code is a
stable, human-authored building number, most likely taken from the source IFC file's own
name (the one sample committed to this repo, `assets/ed_2.ifc`, is plausibly the file for
building `2`). **This inference is not confirmed against the xdtiler ingestion code**
(which lives outside this repo) and should be checked with whoever operates
`metapolis-xdtiler`.

Nothing inside the IFC itself carries this number: `IfcBuilding.Name` is empty, and the
only custom property set (`VeNiss_Phases`, 99 instances) carries just `Phase Created =
'2023'` (→ the manifest's `phase_year`), not an id.

### Georeferencing is also external to the IFC (separate finding, same root cause)

`ed_2.ifc`'s `IFCSITE` entity carries `RefLatitude`/`RefLongitude` of **42°24'53"N,
71°15'29"W — Boston**, a Revit template default, not Venice. The real placement lives in
each building's `tileset.json` as an ECEF translation (e.g. building 13:
`4381582.77, 960165.36, 4519164.27`, correctly in the Venice area). So both the semantic
id *and* the real-world position of every mesh are assigned by a manual, out-of-band step
in the external pipeline, with nothing in the IFC to cross-check against. This is a second,
independent risk surface (wrong footprint placement) alongside the id-mismatch risk below,
worth the xdtiler operator's attention even though it's not, strictly, an "ID" problem.

## The identity chain (as implemented in Map.html)

```
3D manifest:  code=13, isl_code=LZV
   └─(string convention "isl_code + _BLDG_ + code", applied in semantic-map-advanced)
bw_id      = "LZV_BLDG_13"
PostGIS:      veniss_data.identifier = "LZV_BLDG_13"                    Map.html:204
RDF:          ?2drepresentation rdfs:label "LZV_BLDG_13"                Map.html:212
   └─ P138i_has_representation ← phase ← P166i_had_presence ← physical_changes ← P196i_is_defined_by
building_iri = https://veniss.net/resource/builtwork/<uuid>             Map.html:214
```

The terminal building IRI is a stable UUID. The fragility is entirely in the two
**un-enforced string joins** above it: the `{isl}_BLDG_{code}` naming convention, and the
plain string-equality match between the SQL `identifier` and the RDF `rdfs:label`. Neither
is a typed/foreign-key relationship, so nothing prevents a mesh from referencing a `bw_id`
that doesn't exist, or a `bw_id` that resolves to more than one building.

## Findings (full reconciliation, `utils/reconcile_3dtiles.py`)

```
=== LZV: 40 meshes, 85 RDF building codes ===
  ORPHAN meshes (no RDF building, dead click): ['98', '99', '101']
  Buildings with no mesh (coverage gap, informational): [48 codes, e.g. '26','27','32'...]
```

| # | Finding | Class | Detail |
|---|---------|-------|--------|
| F1 | **Orphan meshes: codes `98`, `99`, `101`.** No node of *any* type in the store carries `LZV_BLDG_98`, `LZV_BLDG_99`, or `LZV_BLDG_101` (not even a bare `crm:E42_Identifier`). Clicking these three meshes on the map resolves to nothing. | Missing data or filename typo | Needs a human decision (create the building record, or the mesh is mislabeled) — a script shouldn't guess. |
| F2 | **Silent mislink (latent risk, not yet observed).** Because the id is filename-derived with no cross-check, a filename typo pointing at a *valid* building number (e.g. meant `21`, typed `12`) would attach the wrong mesh to the wrong building with **no error anywhere in the pipeline**. Not currently detectable from data alone — flagged as a design gap. | Design gap | See fix design V2/V3. |
| F3 | **Coverage gap:** 48 of LZV's 85 RDF building codes have no 3D mesh. Not an error (partial modeling campaign), but must be surfaced, not silently absent. | Informational | Reporting only. |
| F4 | **Duplicate builtworks sharing one label (12 cases, e.g. `PVG_BLDG_2` → both a curated "Laundry Pavillion" record and an unlabeled stub still named `PVG_BLDG_2`).** Root cause: duplicate ingests split across `https://veniss.net/resource/builtwork/…` and `http://www.researchspace.org/resource/builtwork/…`. Currently **0 LZV codes are ambiguous** (37 of 40 meshes resolve to exactly one building), but this will bite the moment PVG or SSC get a 3D tileset. | Data de-dup, out of scope for IFC-processing fixes | Separate production-write cleanup. |
| F5 | Unrelated to 3D: the Islands `<features-layer>` mints subjects as `IRI(CONCAT('http://veniss.net/resource/', ?bw_id))` (`Map.html:288`) using **`http://`**, while the canonical namespace (`config/namespaces.prop`) is **`https://`**. | Template bug | One-line fix, separate PR. |

**Bottom line:** the id *generation* is sound (stable, human-authored numbers, not
row-order). All three observed failures on LZV are "mesh present, semantic record absent"
(F1) — zero ambiguous matches today. The design has no way to catch a typo pointing at a
*valid but wrong* building (F2) until it happens.

## Recommended fixes at IFC-processing time

These target the external `metapolis-xdtiler` pipeline; V5 is already implemented in this
repo as a stopgap that needs no upstream changes.

- **V1 — Registration gate.** Before publishing a manifest, for each `{isl}_BLDG_{code}`
  run the `COUNT(DISTINCT ?b)` query used above: `0` → orphan, quarantine the mesh (exclude
  from the published manifest or mark `"linked": false`); `>1` → ambiguous, quarantine and
  flag for de-dup; `1` → publish. (Using a boolean `ASK` here is insufficient — it can't
  distinguish "exactly one match" from "matched, but ambiguously.") Would have caught 98/99/101
  before publish.
- **V2 — Embedded-ID cross-check.** Authoring convention: store the code *inside* the IFC
  (`IfcBuilding.Name = "LZV_BLDG_98"`, or a `VeNiss_ID` property alongside the existing
  `VeNiss_Phases` pset). The tiler parses it and hard-fails on filename↔embedded mismatch.
  This is the only layer that catches a typo pointing at a *valid* building (F2), but only
  for newly-authored files.
- **V3 — Geometric plausibility check (retroactive, no re-authoring needed).** Each
  building's `tileset.json` already carries an ECEF placement transform and bounding
  volume. Convert to EPSG:3857, compare centroid/footprint against the PostGIS geometry of
  the claimed `bw_id` (`PRODUCTION.veniss_data` via the `production` geosql query); flag if
  they don't overlap within a tolerance. Works on the existing 40 LZV files today, and also
  catches the georeferencing risk noted above, not just id typos.
- **V4 — Manifest enrichment.** Once V1 resolves a code, have the tiler write the resolved
  `bw_id` (and ideally `building_iri`) directly into the manifest, so `semantic-map-advanced`
  reads it instead of reconstructing `{isl}_BLDG_{code}` by convention in the frontend.
  Requires an upstream change in `metapolis-xdtiler` plus the map component.
- **V5 — `utils/reconcile_3dtiles.py` (implemented in this PR).** Read-only, runs today
  against every published island manifest, reports orphans/ambiguous/coverage gaps, exits
  non-zero on orphans or ambiguity. Packages V1's check without needing any upstream
  change — run it after every re-tiling, or in CI once one exists.

## Out of scope for this audit (flagged, not fixed here)

- F4 duplicate-builtwork de-dup and the `researchspace.org`/`veniss.net` namespace split:
  production RDF writes, needs per-query typed confirmation per repo convention.
- F5 islands `http://`→`https://` fix: unrelated template one-liner.
