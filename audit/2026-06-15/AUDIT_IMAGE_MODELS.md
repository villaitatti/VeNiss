# Audit: Image model alignment (filename resolution + TIFF)

**Date:** 2026-06-15
**Scope:** All `rso:EX_Digital_Image` resources and how they resolve a literal filename
**Tool:** SPARQL via the **mcp-sparql** MCP server (run from the workspace root where
`.claude/mcp.json` loads it — **never curl**). Blazegraph is **production**.
**Rule:** `SELECT`/`ASK` are read-only and safe. Every `INSERT`/`DELETE` requires **typed
per-query confirmation** before execution.

Prefixes used throughout:
```sparql
PREFIX crm:    <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX rso:    <http://www.researchspace.org/ontology/>
PREFIX rs:     <http://www.researchspace.org/ontology/>
PREFIX crmdig: <http://www.ics.forth.gr/isl/CRMdig/>
PREFIX xsd:    <http://www.w3.org/2001/XMLSchema#>
```

## Background
Images reach their filename literal (`rso:PX_has_file_name`) via two models:
- **Model A:** `?img crm:P1_is_identified_by/rso:PX_has_file_name ?name`
- **Model B (dominant):** `?img crmdig:L60i_is_documented_by/crmdig:L11_had_output/rso:PX_has_file_name ?name`

The templates now resolve **both** (Layer A). This audit finds records the templates
still can't fix: filenames stored as IRIs (the preview crash), TIFFs, and orphans.

---

## B1 — Read-only diagnostics

### D1 — Model census (how images resolve a filename)
```sparql
SELECT
  (COUNT(DISTINCT ?img) AS ?totalImages)
  (SUM(?both)    AS ?bothModels)
  (SUM(?aOnly)   AS ?modelA_only)
  (SUM(?bOnly)   AS ?modelB_only)
  (SUM(?neither) AS ?neither)
WHERE {
  ?img a rso:EX_Digital_Image .
  BIND(EXISTS { ?img crm:P1_is_identified_by/rso:PX_has_file_name ?fa . FILTER(isLiteral(?fa)) } AS ?hasA)
  BIND(EXISTS { ?img crmdig:L60i_is_documented_by/crmdig:L11_had_output/rso:PX_has_file_name ?fb . FILTER(isLiteral(?fb)) } AS ?hasB)
  BIND(IF(?hasA && ?hasB, 1, 0)   AS ?both)
  BIND(IF(?hasA && !?hasB, 1, 0)  AS ?aOnly)
  BIND(IF(!?hasA && ?hasB, 1, 0)  AS ?bOnly)
  BIND(IF(!?hasA && !?hasB, 1, 0) AS ?neither)
}
```
**Result:** _(fill in)_ — expect `modelB_only` to dominate, confirming why the old
Model-A-only patterns failed.

### D2 — Crash class: `PX_has_file_name` is an IRI, not a literal
This is the `…EX_File/…dis.13.tif` preview-crash case.
```sparql
SELECT DISTINCT ?carrier ?badValue WHERE {
  ?img a rso:EX_Digital_Image .
  ?img (crm:P1_is_identified_by|crmdig:L60i_is_documented_by/crmdig:L11_had_output) ?carrier .
  ?carrier rso:PX_has_file_name ?badValue .
  FILTER(!isLiteral(?badValue))
}
```
**Result:** _(fill in — list the carrier nodes and bad IRI values)_

### D3 — TIFF inventory (server-render targets for Cantaloupe)
```sparql
SELECT DISTINCT ?img ?fileName WHERE {
  ?img a rso:EX_Digital_Image .
  ?img (crm:P1_is_identified_by|crmdig:L60i_is_documented_by/crmdig:L11_had_output)/rso:PX_has_file_name ?fileName .
  FILTER(isLiteral(?fileName) && REGEX(STR(?fileName), "\\.tiff?$", "i"))
}
```
**Result:** _(fill in — count + sample names)_

### D4 — Orphans: no literal filename via either model (template cannot fix)
```sparql
SELECT DISTINCT ?img WHERE {
  ?img a rso:EX_Digital_Image .
  FILTER NOT EXISTS {
    ?img (crm:P1_is_identified_by|crmdig:L60i_is_documented_by/crmdig:L11_had_output)/rso:PX_has_file_name ?f .
    FILTER(isLiteral(?f))
  }
}
```
**Result:** _(fill in)_

### D5 — Link-property census (validates the gallery main/more split)
```sparql
SELECT ?prop (COUNT(DISTINCT ?img) AS ?n) WHERE {
  ?entity ?prop ?img . ?img a rso:EX_Digital_Image .
  FILTER(?prop IN (rso:PX_has_main_representation, crm:P138i_has_representation))
} GROUP BY ?prop
```
**Result:** _(fill in — `PX_has_main_representation` = main image KP; `P138i_has_representation` = "more images" KP)_

---

## B2 — Repairs (run ONLY after reviewing D2/D4; each needs typed per-query confirmation)

### R1 — Fix IRI-valued filenames (from D2)
The bad value is the EX_File IRI `…/EX_File/<filename>`; its last path segment IS the
intended filename. **Validate against D2 output first** (confirm every bad value ends in
the real filename before running).
```sparql
DELETE { ?carrier rso:PX_has_file_name ?badIRI }
INSERT { ?carrier rso:PX_has_file_name ?literalName }
WHERE {
  ?carrier rso:PX_has_file_name ?badIRI .
  FILTER(!isLiteral(?badIRI))
  BIND(STRDT(REPLACE(STR(?badIRI), "^.*/(.*)$", "$1"), xsd:string) AS ?literalName)
}
```
**Verify:** re-run **D2** → expect 0 rows.

### R2 — Orphans (from D4)
No safe blanket fix. For each orphan decide: reconnect to its `EX_File` via the canonical
path, or accept it as genuinely fileless. **List decisions here** before any `INSERT`.

---

## Outcome checklist
- [ ] D1-D5 run; results recorded above.
- [ ] R1 confirmed + executed; D2 re-run = 0.
- [ ] D4 orphans triaged.
- [ ] Spot-check repaired entities in the UI (preview modal renders, no "Invalid image ID").
- [ ] D3 TIFFs render once Cantaloupe is live (see `deploy/cantaloupe/README.md`).
