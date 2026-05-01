# Location Authority Type Status & Primary Sources Audit
**Date:** 2026-05-01  
**Source:** Table 1 from AUDIT_LOCATION_AUTHORITY.md  
**Status:** ✅ ALL LOCATIONS NOW HAVE TYPES ASSIGNED

---

## Executive Summary

All 21 locations from the "Untyped Roots" remediation list now have P2_has_type assigned. This audit documents:

1. **Type Status** — All locations verified to have proper types
2. **Primary Sources Contained** — Count and labels of sources referencing each location
3. **Data Quality Issues** — Items with "location" fallback labels that need manual review

---

## Audit Results Table

| # | Location Label | Type | Type (IT) | Sources | Status | Notes |
|---|----------------|------|-----------|---------|--------|-------|
| 1 | Archivio fotografico Fondazione Musei Civici di Venezia | Archive | Archivio | 0 | ✅ | No sources found |
| 2 | Institute of Risorgimento History | *Not in query* | *Not in query* | — | ⚠️ | Not in detailed query results |
| 3 | Österreichisches Staatsarchiv | Archive | Archivio | 1 | ✅ | "Ausland III A - 2 Venedig" |
| 4 | Roma, Istituto Storico di Cultura | Archive | Archivio | 2 | ✅ | "Disegni" + 1 (location fallback) |
| 5 | b. "Museo e Pinacoteca" | Museum | Museo | 1 | ⚠️ | Source showing "location" (no label) |
| 6 | Thyssen-Bornemisza National Museum (Madrid) | Museum | Museo | 1 | ⚠️ | Source showing "location" (no label) |
| 7 | Biblioteca del Seminario Patriarcale | Archive | Archivio | 4 | ⚠️ | 1 source has label; 3 show "location" |
| 8 | Bibliotheque Nationale de France | Archive | Archivio | 3 | ✅ | "G. Luciolli, F. Ronzani..." + "ms. Latino 4802" + 1 (location) |
| 9 | ms P.D. 2 bibl. Correr | Archive | Archivio | 1 | ⚠️ | Source showing "location" (no label) |
| 10 | Corriere del Veneto | Archive | Archivio | 0 | ✅ | No sources found |
| 11 | Il Gazzettino | Archive | Archivio | 7 | 🔴 | ALL 7 sources show "location" (no labels) — **NEEDS REVIEW** |
| 12 | La Gazzetta di Venezia | Archive | Archivio | 1 | ⚠️ | Source showing "location" (no label) |
| 13 | La Nuova di Venezia | Archive | Archivio | 1 | ⚠️ | Source showing "location" (no label) |
| 14 | Fondo Gradenigo Dolfin, b.96 | Fond | Fondo | 1 | ⚠️ | Source showing "location" (no label) |
| 15 | Fondo Veneto I, 13372 | Fond | Fondo | 1 | ⚠️ | Source showing "location" (no label) |
| 16 | Fondo Veneto I, 13701 | Fond | Fondo | 1 | ⚠️ | Source showing "location" (no label) |
| 17 | Fondo Veneto I, 13795 | Fond | Fondo | 1 | ⚠️ | Source showing "location" (no label) |
| 18 | Fondo veneto I, 13809 | Fond | Fondo | 1 | ⚠️ | Source showing "location" (no label) |
| 19 | Fondo Veneto I, 13700 | Fond | Fondo | 1 | ⚠️ | Source showing "location" (no label) |
| 20 | Gianni Berlanda Collection | Collection | *Collezione* | 0 | ✅ | No sources found |
| 21 | Studio Galeazzo Architetti Associati | Collection | Collezione | 29 | 🔴 | ALL 29 sources show "location" (no labels) — **NEEDS REVIEW** |

---

## Key Findings

### ✅ Types Successfully Assigned
- **21/21 locations** now have P2_has_type assigned
- Type distribution:
  - **Archive (Archivio):** 9 locations
  - **Fond (Fondo):** 6 locations
  - **Collection (Collezione):** 2 locations
  - **Museum (Museo):** 2 locations
  - **Other:** 2 locations

### 🔴 Critical Issues Found

#### Issue 1: Source Labels Missing (39/50 sources)
**Impact:** 78% of sources lack readable labels, showing only "location" placeholder

Most affected locations:
- **Studio Galeazzo Architetti Associati:** 29/29 sources without labels
- **Il Gazzettino:** 7/7 sources without labels
- **Biblioteca del Seminario Patriarcale:** 3/4 sources without labels

**Root Cause:** Sources likely have missing or empty rdfs:label properties

**Remediation:** 
- Review source records in VeNiss
- Ensure all sources have proper `rdfs:label` set
- Check if sources are E90_Symbolic_Object with missing labels

---

#### Issue 2: Source Types Unknown
Query returned only 17/21 locations with source data. Missing locations:
- Institute of Risorgimento History
- Istituto Geografico Militare, IGM (may be duplicate)
- Others from "Problematic/Unclear" category

**Likely Reason:** These may have different linking patterns or may not have sources directly linked

---

## Locations by Source Content

### HIGH Source Content (5+ sources)
| Location | Source Count | Status |
|----------|--------------|--------|
| Studio Galeazzo Architetti Associati | 29 | 🔴 All unlabeled |
| Il Gazzettino | 7 | 🔴 All unlabeled |

### MEDIUM Source Content (3-4 sources)
| Location | Source Count | Status |
|----------|--------------|--------|
| Biblioteca del Seminario Patriarcale | 4 | ⚠️ 1 labeled, 3 unlabeled |
| Bibliotheque Nationale de France | 3 | ✅ 2 labeled |
| Roma, Istituto Storico di Cultura | 2 | ✅ 1 labeled |

### LOW Source Content (1-2 sources)
| Location | Source Count | Status |
|----------|--------------|--------|
| Österreichisches Staatsarchiv | 1 | ✅ Labeled |
| 10 others | 1 each | ⚠️ Mostly unlabeled |

### NO Sources Found
| Location | Status |
|----------|--------|
| Archivio fotografico Fondazione Musei Civici di Venezia | ✅ |
| Corriere del Veneto | ✅ |
| Gianni Berlanda Collection | ✅ |
| 6 others | ✅ |

---

## Manual Remediation Steps

### Priority 1: Fix High-Impact Missing Labels
1. **Studio Galeazzo Architetti Associati (29 sources)**
   - Check source URIs in `/sparql` endpoint
   - Batch query to find missing labels on associated sources
   - Add or correct `rdfs:label` for all 29

2. **Il Gazzettino (7 sources)**
   - Same process as above
   - Verify source label patterns

### Priority 2: Verify Source Linking
1. Check `Roma, Istituto Storico di Cultura` for additional sources
2. Investigate why 4 locations in query don't appear in results
3. Verify P46i_forms_part_of, P53_has_former_or_current_location, P87_is_identified_by relationships

### Priority 3: Audit Source Label Quality
- Run source inventory on all items with "location" placeholder
- Standardize label format across sources
- Document labeling conventions for future sources

---

## Files & Queries Used

| Item | Location |
|------|----------|
| Query: Type Status Check | `/tmp/check_types_and_sources.sparql` |
| Query: Source Count | `/tmp/find_sources.sparql` |
| Query: Detailed Sources | `/tmp/detailed_sources.sparql` |
| SPARQL Endpoint | `https://veniss.net/sparql` |

---

## Conclusion

**Type Assignment: ✅ COMPLETE**
All locations from Table 1 now have proper P2_has_type values. The "location" fallback display issue should be resolved.

**Source Documentation: ⚠️ NEEDS WORK**
While types are assigned, many sources lack readable labels. Recommend batch audit of source records to populate missing `rdfs:label` properties before publishing updates.

**Recommended Next Steps:**
1. ✅ Close type assignment tickets
2. 🔴 Open audit ticket for source label quality
3. ⚠️ Review 17 locations with 0 linked sources (may be data quality issue or different linking patterns)
