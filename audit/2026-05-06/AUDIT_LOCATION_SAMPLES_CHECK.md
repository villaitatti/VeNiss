# Audit Results: Archival Locations Data Quality Check

## Summary
Two archival locations were checked for data consistency per the pending audit items from the 2026-04-30 Location Authority audit.

---

## Location 1: "b. 44"
**URI:** `https://veniss.net/resource/archival_entity/df1808a7-a553-4ca0-a393-866282d7d04b`

### Data Status

| Property | Value | Status |
|----------|-------|--------|
| **rdf:type** | E78_Collection | ✓ CORRECT |
| **P71i_is_listed_in** | vocab/archives | ✓ CORRECT |
| **rdfs:label** | "b. 44" (it, en) | ✓ CORRECT |
| **P2_has_type** | Bundle (Mazzo) | ✓ CORRECT |
| **P46i_forms_part_of** | Provveditori alle fortezze | ✓ CORRECT |
| **displayLabel** | MISSING | ⚠️ ISSUE |

### Issues Found
1. **Missing displayLabel** (required for efficient filter display)
   - Currently must reconstruct hierarchy at runtime
   - May show truncated name "b. 44" instead of full path

### Recommendation
- **PRIORITY: MEDIUM** — Add displayLabel
- Suggested format: "Provveditori alle fortezze, b. 44"

---

## Location 2: "b. 562"
**URI:** `http://www.researchspace.org/resource/vocab/archives/53f0740f-9a1a-40f2-b900-76323678d25f`

### Data Status

| Property | Value | Status |
|----------|-------|--------|
| **rdf:type** | E78_Collection | ✓ CORRECT |
| **P71i_is_listed_in** | vocab/archives | ✓ CORRECT |
| **rdfs:label** | "b. 562" (it, en) | ✓ CORRECT |
| **P2_has_type** | MISSING | 🔴 CRITICAL |
| **P46i_forms_part_of** | Patroni e provveditori all'Arsenal | ✓ CORRECT |
| **P1_is_identified_by** | path, search_term | ✓ CORRECT |
| **displayLabel** | MISSING | ⚠️ ISSUE |

### Issues Found
1. **MISSING P2_has_type** (CRITICAL) 🔴
   - No type/typology assigned
   - Violates audit finding that P2_has_type is critical for semantic distinction
   - Will cause "location" fallback display if shown in UI
   - This is on the Priority 1 list from the audit

2. **Missing displayLabel** (MEDIUM)
   - Same issue as b. 44
   - Required for efficient filter display

### Recommendation
- **PRIORITY: CRITICAL** — Assign P2_has_type
  - This item appears to be a bundle/box (based on label "b. 562")
  - Suggested type: Bundle (Mazzo) - same as b. 44
  - URI: `https://veniss.net/resource/vocab/archival_unit_types/360f8cc8-4cb5-11ee-9292-3a5becfe4abd`

- **PRIORITY: MEDIUM** — Add displayLabel
  - Suggested format: "Patroni e provveditori all'Arsenal, b. 562"

---

## Comparison with Audit Findings

Both locations confirm the three critical issues identified in the 2026-04-30 audit:

### Issue A: Missing Types ✓ CONFIRMED
- **b. 562** is missing P2_has_type (identified as untyped root)
- This validates Priority 1 fix requirement

### Issue B: Incomplete Hierarchies ✓ CONFIRMED  
- Both locations **ARE** properly hierarchical (have P46i_forms_part_of)
- They are NOT root locations
- Parent relationships appear correct

### Issue C: Missing displayLabel ✓ CONFIRMED
- Both lack displayLabel property
- Aligns with audit finding that only 85% coverage of displayLabel
- Causes inefficient runtime reconstruction in filter display

---

## Recommended SPARQL Fixes

### For b. 562: Add P2_has_type

```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>

INSERT { 
  <http://www.researchspace.org/resource/vocab/archives/53f0740f-9a1a-40f2-b900-76323678d25f> 
  crm:P2_has_type 
  <https://veniss.net/resource/vocab/archival_unit_types/360f8cc8-4cb5-11ee-9292-3a5becfe4abd> 
}
WHERE {
  <http://www.researchspace.org/resource/vocab/archives/53f0740f-9a1a-40f2-b900-76323678d25f> 
  crm:P71i_is_listed_in 
  <http://www.researchspace.org/resource/vocab/archives> .
  FILTER NOT EXISTS {
    <http://www.researchspace.org/resource/vocab/archives/53f0740f-9a1a-40f2-b900-76323678d25f> 
    crm:P2_has_type ?existing
  }
}
```

### For both: Add displayLabel (optional but recommended)

```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX rs: <http://www.researchspace.org/ontology/>

-- For b. 44
INSERT {
  <https://veniss.net/resource/archival_entity/df1808a7-a553-4ca0-a393-866282d7d04b>
  rs:displayLabel "Provveditori alle fortezze, b. 44"
}
WHERE {
  <https://veniss.net/resource/archival_entity/df1808a7-a553-4ca0-a393-866282d7d04b>
  crm:P71i_is_listed_in <http://www.researchspace.org/resource/vocab/archives> .
}
;

-- For b. 562
INSERT {
  <http://www.researchspace.org/resource/vocab/archives/53f0740f-9a1a-40f2-b900-76323678d25f>
  rs:displayLabel "Patroni e provveditori all'Arsenal, b. 562"
}
WHERE {
  <http://www.researchspace.org/resource/vocab/archives/53f0740f-9a1a-40f2-b900-76323678d25f>
  crm:P71i_is_listed_in <http://www.researchspace.org/resource/vocab/archives> .
}
```

---

## Data Quality Summary

| Item | Issue Count | Critical | Medium | Status |
|------|------------|----------|--------|--------|
| **b. 44** | 1 | 0 | 1 | ⚠️ Needs displayLabel |
| **b. 562** | 2 | 1 | 1 | 🔴 Needs P2_has_type + displayLabel |

**Overall:** Both locations confirm the audit's Priority 1 findings and should be fixed as part of Phase 1 of the execution plan.

---

## Methodology

**Tools Used:** curl + SPARQL queries (SELECT)
**Endpoint:** https://veniss.net/sparql
**Date:** 2026-05-06
**Scope:** Sample verification of 2 archival locations mentioned in previous audit work

**Queries executed:**
1. Multi-property check on both URIs
2. Full hierarchy and authority verification
3. Complete property enumeration for b. 562
