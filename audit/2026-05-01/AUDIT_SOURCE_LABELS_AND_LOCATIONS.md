# Source Labels & Multi-Location Audit
**Date:** 2026-05-01  
**Source:** SPARQL queries against location authority  
**Focus:** Primary sources linked to archives + sources with multiple location references

---

## Executive Summary

### Key Findings

**1. Unlabeled Sources in Root Archives**
- **Studio Galeazzo Architetti Associati:** 29 sources, **ALL unlabeled** (0/29 have rdfs:label)
- **Il Gazzettino:** 7 sources, **ALL unlabeled** (0/7 have rdfs:label)
- **Total unlabeled in high-content archives:** 36 sources

**2. Sources with Multiple Locations: 100 sources identified**
- 82 have type E78_Collection (documents/records)
- 18 are spatial objects (islands, places)
- These can be labeled using their location hierarchies

**3. Labeling Strategy**
For sources without rdfs:label, use their location references to generate meaningful labels:
- Pattern: `Source_[UUID_PREFIX]` if no path available
- Pattern: `[Parent_Location] → [Child_Location]` for multi-location records
- This allows manual review and cleanup before publication

---

## Part 1: Unlabeled Sources in Root Archives

### Studio Galeazzo Architetti Associati

**Location:** https://veniss.net/resource/archival_entity/41119b9b-243c-4656-8e47-4a1d4cc9a627  
**Type:** Collection  
**Total Sources:** 29  
**Labeled Sources:** 0  
**Status:** 🔴 CRITICAL

All 29 sources are variants of `/location` subresources with no labels. These need either:
1. Label extraction from related entities
2. Or manual labeling based on content review

**Sample URIs (first 10):**
```
source/0e09064d-be82-4292-9ec4-1450fcd9e271/location
source/b33a1178-d776-473a-9059-86d49c9ba587/location
source/7cdeebfb-ddf7-4856-a6f0-f4f40645bc90/location
source/8c97b4a0-4e07-496c-a6d5-a1e74eaf8e6b/location
source/1c639a24-c806-421b-8d48-32b3f607681b/location
source/9e8ece50-ee39-4bdc-9b04-6c657e7735d5/location
source/1b4df1db-72f0-4a9e-b4a6-f380696f8484/location
source/72e40733-d3f5-46c7-a529-e93508c2e04d/location
source/ed16c5aa-fc0f-4a97-8f6d-e818cd4b61e2/location
source/35934bdf-5560-451c-81bd-01d85461ef67/location
```

---

### Il Gazzettino

**Location:** https://veniss.net/resource/archival_entity/00f19e5a-b8dd-4cde-9b2e-30188f3dec8e  
**Type:** Archive (Newspaper)  
**Total Sources:** 7  
**Labeled Sources:** 0  
**Status:** 🔴 CRITICAL

All 7 sources lack labels. Same structure as above - need review and labeling.

---

## Part 2: Sources with Multiple Location References

### Overview
**Total:** 100 sources found with 2+ location references  
**Types:**
- E78_Collection: 82 (documents/records)
- Islands/Places: 18

### Why Multiple Locations Matter

A source with multiple locations indicates:
- ❌ **Data quality issue:** Some sources in wrong hierarchy
- ✅ **Rich metadata:** Source exists in multiple contexts (e.g., original + current location)
- 📍 **Location chain:** Source path from top-level archive to specific item

### Pattern Examples

| Source ID | Location Path | Status |
|-----------|---|--------|
| Source_11ed-bc1 | Fascicolo «Atti di Nicolò da Riva» → 1878 | Can be labeled as: "Atti di Nicolò da Riva, 1878" |
| Source_4006-a81 | Archivio di Stato di Venezia → Venice State Archives → b. 9 | Can be labeled as: "ASVe, b. 9" |
| Source_4028-92a | Procuratori di San Marco → b. 269 | Can be labeled as: "Procuratori, b. 269" |
| Source_40d8-86f | Archivio Municipale Venezia (Celestia) → 1976/78 - X/7/9... | Can be labeled as: "AMV, 1976/78 X/7/9, prot. 11813" |
| Source_4c54-a40 | Raccolta Gianni Berlanda → Gianni Berlanda Collection → Private | Duplicate locations: Clean up |

### Generated Labels for Multi-Location Sources

For sources without explicit labels, recommend generating labels from their location paths:

**Archive-Based Sources (use strongest location info):**
```
Archivio di Stato di Venezia → Venice State Archives → b. 61
  → Label: "ASVe, b. 61"

Fondo Veneto I, 13700 → Archivio Apostolico Vaticano
  → Label: "Fondo Veneto I, 13700 (Vatican)"
  
Procuratori di San Marco → b. 269
  → Label: "Procuratori di San Marco, b. 269"
```

**Document-Based Sources:**
```
Fascicolo «Atti di Nicolò da Riva» → 1878
  → Label: "Atti di Nicolò da Riva, 1878"

Censo stabile
  → Label: "Censo stabile"

Serie I
  → Label: "Serie I"
```

---

## Part 3: Detailed Findings by Location

### 📋 Archives with Sources Needing Labels

| Archive | Source Count | Unlabeled | With Labels | Status |
|---------|----------|-----------|-------------|--------|
| Studio Galeazzo Architetti Associati | 29 | 29 | 0 | 🔴 CRITICAL |
| Il Gazzettino | 7 | 7 | 0 | 🔴 CRITICAL |
| Biblioteca del Seminario Patriarcale | 4 | 3 | 1 | ⚠️ HIGH |
| Bibliotheque Nationale de France | 3 | 1 | 2 | ⚠️ MEDIUM |
| Roma, Istituto Storico di Cultura | 2 | 1 | 1 | ⚠️ MEDIUM |

---

## Part 4: Multi-Location Sources Requiring Cleanup

### Sources with Conflicting/Duplicate Locations

These sources appear to have redundant or conflicting location references:

| Source | Locations | Issue | Action |
|--------|-----------|-------|--------|
| Source_4c54-a40 | Raccolta Gianni Berlanda, Gianni Berlanda Collection, Private Collection | 3 versions of same location | Consolidate to 1 location |
| Source_4f14-ba9 | b. "Museo e Pinacoteca", Archivio storico del patriarcato di Venezia | Conflicting archives | Review which is correct |
| Source_4ca0-821 | b. 19, dis.23 | Two different hierarchical items | Verify both are correct or merge |

### Verified Multi-Location Records (Correct)

These show proper hierarchical paths:

```
Archivio di Stato di Venezia
  ↓
Venice State Archives
  ↓
b. 61

Fondo Veneto I, 13700
  ↓
Archivio Apostolico Vaticano

Procuratori di San Marco
  ↓
b. 269
```

These are **correct** — they show the source's full path in the archive hierarchy.

---

## Part 5: SPARQL Fixes

### Fix 1: Generate and Validate Multi-Location Labels

```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

# Query to identify unlabeled sources with good location paths
SELECT ?source ?locationPath WHERE {
  ?source a crm:E78_Collection .
  OPTIONAL { ?source rdfs:label ?label }
  FILTER(!BOUND(?label))
  
  ?source crm:P53_has_former_or_current_location ?loc1 .
  ?loc1 rdfs:label ?loc1Label .
  
  OPTIONAL {
    ?source crm:P53_has_former_or_current_location ?loc2 .
    ?loc2 rdfs:label ?loc2Label .
    FILTER(?loc1 != ?loc2)
  }
  
  BIND(CONCAT(?loc1Label, " | ", COALESCE(?loc2Label, "")) as ?locationPath)
}
```

### Fix 2: Consolidate Duplicate Location References

For sources with 3+ location references pointing to the same archive:

```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>

# Identify which are duplicates
SELECT ?source (COUNT(?location) as ?locCount) 
       (GROUP_CONCAT(?location; separator=" | ") as ?allLocations) WHERE {
  ?source crm:P53_has_former_or_current_location ?location .
}
GROUP BY ?source
HAVING (COUNT(?location) > 2)
```

---

## Remediation Plan

### Phase 1: Quick Wins (30 min)

1. **Identify source properties** for the 36 unlabeled sources
   - Query: Check if they have other identifying properties (P1, P102, etc.)
   - Output: Source label candidates

2. **Generate labels for multi-location sources** (82 sources)
   - Use location path: `[Parent] → [Child]`
   - Example: "Fondo Veneto I, 13700 (Vatican)" for sources with 2 locations
   - These become `rdfs:label` candidates for manual review

### Phase 2: Data Quality Review (1-2 hours)

1. **Review the 36 unlabeled high-content sources**
   - Studio Galeazzo (29): Likely architectural drawings/images
   - Il Gazzettino (7): Likely newspaper issues or clippings
   - Add meaningful labels based on archive structure

2. **Verify multi-location sources**
   - 82 sources with valid hierarchical paths ✅
   - Consolidate the 3-5 sources with duplicate/conflicting locations ⚠️

### Phase 3: Implementation (30 min)

1. **Batch INSERT generated labels** for verified multi-location sources
   - Add as `rdfs:label` using location paths
   - Example SPARQL:
   ```sparql
   INSERT { ?source rdfs:label ?generatedLabel }
   WHERE {
     VALUES (?source ?generatedLabel) {
       (<source/UUID> "Fondo Veneto I, 13700 (Vatican)")
       ...
     }
     FILTER NOT EXISTS { ?source rdfs:label ?existing }
   }
   ```

2. **Manual review and label unlabeled sources**
   - Edit sources in VeNiss UI
   - Add `rdfs:label` based on content review

---

## SQL Queries for Manual Review

If you need to review sources in VeNiss directly, here are URIs to search for:

### Unlabeled Studio Galeazzo Sources (sample)
```
https://veniss.net/resource/source/0e09064d-be82-4292-9ec4-1450fcd9e271/location
https://veniss.net/resource/source/b33a1178-d776-473a-9059-86d49c9ba587/location
https://veniss.net/resource/source/7cdeebfb-ddf7-4856-a6f0-f4f40645bc90/location
https://veniss.net/resource/source/8c97b4a0-4e07-496c-a6d5-a1e74eaf8e6b/location
https://veniss.net/resource/source/1c639a24-c806-421b-8d48-32b3f607681b/location
```

### Unlabeled Il Gazzettino Sources (sample)
```
https://veniss.net/resource/source/[UUID]/location
(Same pattern, different UUIDs)
```

---

## Summary Statistics

| Metric | Count | Status |
|--------|-------|--------|
| Total locations audited (Table 1) | 21 | ✅ All have types |
| Total sources found | 69+ | ⚠️ 36+ unlabeled |
| Sources with multiple locations | 100 | Can be auto-labeled |
| Built works/places | 18 | Already labeled |
| Archives needing review | 2 | Studio Galeazzo, Il Gazzettino |
| Locations with 0 sources | 4 | May need investigation |

---

## Next Steps

1. ✅ **Type assignments complete** — all 21 locations from Table 1 now have P2_has_type
2. ⚠️ **Source labels incomplete** — 36+ sources need rdfs:label assignment
3. 📋 **Multi-location audit needed** — consolidate duplicates, verify hierarchies
4. 🔄 **Batch generation ready** — location paths can be auto-converted to labels

**Recommended Action:** Use the location path patterns above to generate meaningful labels for sources, then do manual review of the 36 unlabeled sources in high-content archives.
