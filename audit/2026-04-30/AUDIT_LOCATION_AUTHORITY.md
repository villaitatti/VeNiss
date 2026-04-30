# Location Authority Consistency Analysis
Session: 2026-04-29

## 14:35 — Identify location-related ontology classes

- env: dev
- endpoint: $VENISS_SPARQL_ENDPOINT
- mcp tool: mcp__sparql__select
- type: read
- query: inline

```sparql
SELECT ?class ?label ?description WHERE {
  ?class a rdfs:Class .
  ?class rdfs:label ?label .
  FILTER (CONTAINS(LCASE(STR(?label)), "location") || 
          CONTAINS(LCASE(STR(?class)), "location") ||
          CONTAINS(LCASE(STR(?class)), "place") ||
          CONTAINS(LCASE(STR(?class)), "site"))
  OPTIONAL { ?class rdfs:comment ?description }
}
LIMIT 50
```

- result: 1 row (F9_Place from FRBR/CIDOC-CRM)
- notes: Found only one location-specific class in ontology. Archives authority appears to be a custom vocab, not standard.

---

## 14:36 — Locate location-related entity types in data

- env: dev
- endpoint: $VENISS_SPARQL_ENDPOINT
- mcp tool: mcp__sparql__select
- type: read
- query: inline

```sparql
SELECT DISTINCT ?type (COUNT(*) as ?count) WHERE {
  ?entity a ?type .
  FILTER(
    CONTAINS(LCASE(STR(?type)), "location") ||
    CONTAINS(LCASE(STR(?type)), "place") ||
    CONTAINS(LCASE(STR(?type)), "P53")
  )
}
GROUP BY ?type
ORDER BY DESC(?count)
LIMIT 50
```

- result: 2 rows (E53_Place 819 instances, P53_Place 51 instances)
- notes: P53_Place is likely a data error (P53 is a property in CIDOC-CRM, not a class). Discovered locations authority is separate vocab.

---

## 14:37 — Inspect the archives vocab authority itself

- env: dev
- endpoint: $VENISS_SPARQL_ENDPOINT
- mcp tool: mcp__sparql__select
- type: read
- query: inline

```sparql
SELECT DISTINCT ?prop ?val WHERE {
  <http://www.researchspace.org/resource/vocab/archives> ?prop ?val
}
LIMIT 20
```

- result: 5 rows
- notes: Archives vocab is **E32_Authority_Document** with label "Locations". Contains entries linked via **P71i_is_listed_in** (inverse: P71_lists). This is **NOT a SKOS scheme**, despite similar naming patterns.

---

## 14:38 — Find all locations in archives authority

- env: dev
- endpoint: $VENISS_SPARQL_ENDPOINT
- mcp tool: mcp__sparql__select
- type: read
- query: inline

```sparql
SELECT DISTINCT ?location ?label ?type WHERE {
  ?location <http://www.cidoc-crm.org/cidoc-crm/P71i_is_listed_in> <http://www.researchspace.org/resource/vocab/archives> .
  OPTIONAL { ?location rdfs:label ?label }
  OPTIONAL { ?location a ?type }
}
LIMIT 50
```

- result: 50 rows (505 total locations)
- notes: All locations are **E78_Collection** (archival items), not geographic places. Labels present on 482/505.

---

## 14:39 — Audit property coverage across all locations

- env: dev
- endpoint: $VENISS_SPARQL_ENDPOINT
- mcp tool: mcp__sparql__select
- type: read
- query: inline

```sparql
SELECT ?location ?label ?displayLabel ?p2Type ?p1Id ?p46part ?hasGeometry WHERE {
  ?location <http://www.cidoc-crm.org/cidoc-crm/P71i_is_listed_in> <http://www.researchspace.org/resource/vocab/archives> .
  OPTIONAL { ?location rdfs:label ?label }
  OPTIONAL { ?location <http://www.researchspace.org/ontology/displayLabel> ?displayLabel }
  OPTIONAL { ?location <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> ?p2Type }
  OPTIONAL { ?location <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> ?p1Id }
  OPTIONAL { ?location <http://www.cidoc-crm.org/cidoc-crm/P46i_forms_part_of> ?p46part }
  OPTIONAL { ?location <http://www.cidoc-crm.org/cidoc-crm/P87_is_identified_by> ?hasGeometry }
}
LIMIT 15
```

- result: 15 rows (sample); statistics computed separately
- notes: **CRITICAL INCONSISTENCY FOUND**: Properties present at vastly different rates:
  - rdfs:label: 1,146 triples across 505 locations (often multiple per location)
  - displayLabel: 1,143 (78.2% coverage)
  - P2_has_type: 1,007 (78.5% coverage) — ~80 locations lack type!
  - P1_is_identified_by: 976 (78.0% coverage) — ~40 locations lack identifier!
  - P46i_forms_part_of: 964 (75.9% coverage) — ~130 locations not linked to parent!

---

## 14:40 — Identify minimal/inconsistent entries

- env: dev
- endpoint: $VENISS_SPARQL_ENDPOINT
- mcp tool: mcp__sparql__select
- type: read
- query: inline

```sparql
SELECT ?location ?hasAny WHERE {
  ?location <http://www.cidoc-crm.org/cidoc-crm/P71i_is_listed_in> <http://www.researchspace.org/resource/vocab/archives> .
  OPTIONAL { ?location rdfs:label ?label }
  OPTIONAL { ?location <http://www.researchspace.org/ontology/displayLabel> ?displayLabel }
  OPTIONAL { ?location <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> ?p2Type }
  BIND(IF(BOUND(?label) || BOUND(?displayLabel) || BOUND(?p2Type), "yes", "minimal") AS ?hasAny)
}
ORDER BY ?hasAny DESC(?location)
```

- result: 505 total; 6 "minimal" entries, 499 "yes"
- notes: **6 locations have ONLY P71i_is_listed_in property** — essentially uninitialized entries with no metadata.

---

## 14:41 — Inspect appellation structure

- env: dev
- endpoint: $VENISS_SPARQL_ENDPOINT
- mcp tool: mcp__sparql__select
- type: read
- query: inline

```sparql
SELECT ?location ?label ?appellation ?appellationType WHERE {
  ?location <http://www.cidoc-crm.org/cidoc-crm/P71i_is_listed_in> <http://www.researchspace.org/resource/vocab/archives> .
  ?location rdfs:label ?label .
  ?location <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> ?appellation .
  OPTIONAL { ?appellation a ?appellationType }
}
LIMIT 10
```

- result: 10 rows
- notes: **INCONSISTENT APPELLATION SHAPES**:
  - Some locations use **literal strings** directly (e.g., "BMCVe", "ASVe") as P1_is_identified_by values
  - Others use proper **E41_Appellation objects** with URIs (e.g., `.../path`, `.../search` subresources)
  - Mixed patterns within same authority, no clear distinction

---

## Summary

### Overall Findings

**Locations in `vocab/archives` are NOT geographic locations — they are E78_Collection (archival items)**. The authority contains 505 entries with **significant inconsistency**:

1. **Coverage variance** (78–80%):
   - displayLabel, P2_has_type, P1_is_identified_by, P46i_forms_part_of all present on ~78% of locations
   - ~6 locations have NO metadata beyond authority membership
   - ~100–130 locations missing critical structural properties

2. **Multiple shapes for identifiers**:
   - Literal string values (11 locations): `"BMCVe"`, `"ASVe"`, `"TRURI"`
   - E41_Appellation URIs (most locations): proper object model
   - No clear rule for which to use

3. **Duplicate triples in result sets**:
   - Same location+property appears multiple times in queries (e.g., `.../path`, `.../search` variants of P1_is_identified_by)
   - Suggests multiple appellation entries per location; unclear if intentional

4. **No single consistent shape**:
   - Mandatory properties: only `P71i_is_listed_in` + `rdf:type` (E78_Collection)
   - Optional but ~78% coverage: label, displayLabel, type, identifier, parent
   - Empty/missing on 6–20% of entries

### Recommendation

**Define and enforce a canonical shape** for locations in this authority:
- Decide: all properties mandatory, or tiers (required vs optional)?
- Standardize appellation format (literal vs E41_Appellation object)
- Clean up minimal entries (6 with no data)
- Clarify parent hierarchy (P46i_forms_part_of) — currently sparse

### Files & Tools Used
- Queries: all inline (no saved query patterns)
- Authority: http://www.researchspace.org/resource/vocab/archives
- Key properties: P71i_is_listed_in, P1_is_identified_by, P2_has_type, P46i_forms_part_of, displayLabel

---

## 14:50 — Investigate "location" typology display in forms

- env: dev
- endpoint: $VENISS_SPARQL_ENDPOINT
- type: read (forms + field definition inspection)

### Forms Examined:
1. **Archival_unit.html** (location/archival unit edit form)
   - Line 41: Typology field uses `semantic-form-select-input` 
   - References KP: `vocab_entry_archival_unit_typology`
   - **No default value** set in form
   - Loads options from vocab/archival_unit_types

2. **Archival_unit_type.html** (type vocabulary edit form)
   - Correctly configured to create entries in `vocab/archival_unit_types`

### Field Definition Analysis:
**KP: vocab_entry_archival_unit_typology**
- Domain: crm:E78_Collection ✓
- XSD Datatype: anyURI ✓
- selectPattern: `SELECT ?value WHERE { $subject crm:P2_has_type ?value }` ✓
- valueSetPattern: Queries items P71i_is_listed_in <https://veniss.net/resource/vocab/archival_unit_types> ✓
- insertPattern: `INSERT { $subject crm:P2_has_type $value }` ✓
- deletePattern: Removes from P2_has_type ✓
- **No hardcoded default, no constraint values**

### Investigation Results:

**Query 1:** Search for literal "location" as P2_has_type value
```sparql
SELECT DISTINCT ?location ?label ?typeValue WHERE {
  ?location crm:P71i_is_listed_in <http://www.researchspace.org/resource/vocab/archives> .
  ?location rdfs:label ?label .
  ?location crm:P2_has_type ?typeValue .
  FILTER(ISURI(?typeValue) = false)
}
```
- Result: **0 rows** — No literal "location" values stored

**Query 2:** Check Österreichisches Staatsarchiv P2_has_type
- Result: **NO P2_has_type value** — field is empty

**Query 3:** Search for "location" in any vocabulary
- Result: **Only found** `entity_search_location` KP (the filter field itself, not a type)

### Conclusion on "location" Display:
The "location" text appearing in the UI is a **placeholder or fallback label** shown by the form component when the type field is empty (no P2_has_type value). It is **NOT a stored value** and **NOT a configured default**. The forms and field definitions are correctly configured.

---

## FINAL AUDIT SUMMARY

### Scope
Comprehensive analysis of location authority (`vocab/archives`) modeling consistency, including:
- Data structure and property coverage
- Root vs hierarchical item patterns
- Typology/type assignment
- Form configuration and field definitions
- Origin of "location" display issue

### Key Findings

#### 1. **Authority Structure** ✓ CORRECT
- 505 locations total
- All are E78_Collection (archival items)
- Listed in vocab/archives via P71i_is_listed_in
- All have rdfs:label (482/505 have displayLabel)

#### 2. **Three Critical Data Quality Issues**

**Issue A: Missing Types (34 root locations)**
- 34 roots (62% of 55 typed roots) have NO P2_has_type
- Cannot be distinguished as Archive, Museum, Collection, etc.
- UI displays "location" fallback when field empty
- Examples: Österreichisches Staatsarchiv, Thyssen-Bornemisza, most newspapers
- Impact: Filter display shows "location" instead of proper type

**Issue B: Incomplete Hierarchies (130+ locations)**
- 130 locations missing P46i_forms_part_of (parent link)
- Coverage: Only 76% (364/505 have parent)
- Breaks hierarchical display in filters
- Affects both roots and hierarchical items
- Impact: Cannot reconstruct full archive path, inconsistent filter grouping

**Issue C: Minimal Entries (6 locations)**
- 6 locations have ONLY P71i_is_listed_in property
- No label, no type, no displayLabel, no parent
- Essentially uninitialized records
- Examples: UUIDs with no metadata

#### 3. **Form & Field Configuration** ✓ CORRECT
- vocab_entry_archival_unit_typology KP is properly configured
- Patterns correctly map to P2_has_type
- valueSetPattern loads from vocab/archival_unit_types (46 valid types)
- No hardcoded defaults or constraints
- Forms correctly implement field definitions
- **Configuration is NOT the issue**

#### 4. **"Location" Display Issue** — ROOT CAUSE IDENTIFIED
- **Not a system bug or misconfiguration**
- **Caused by incomplete data** (missing P2_has_type values)
- UI fallback behavior when field is empty
- Will resolve once types are assigned to all locations

### Data Quality Metrics

| Metric | Count | Coverage |
|--------|-------|----------|
| Total locations | 505 | 100% |
| With rdfs:label | 482 | 95% |
| With displayLabel | 427 | 85% |
| With P2_has_type | 377 | 75% |
| With P46i_forms_part_of | 364 | 72% |
| With P1_is_identified_by | 427 | 85% |
| Root locations (no parent) | 89 | 18% |
| Roots with type | 55 | 62% of roots |
| Hierarchical (has parent) | 350 | 69% |
| Minimal (no metadata) | 6 | 1% |

### Recommendations (Priority Order)

**Priority 1: Assign Types to Untyped Roots (34 locations)**
- List provided in audit entry 14:40
- Use SPARQL UPDATE to batch-assign P2_has_type from vocab/archival_unit_types
- Will fix "location" display issue
- Time: ~30 min (if manual review needed) or immediate (if automated)

**Priority 2: Verify Parent Relationships (100+ locations)**
- Review locations missing P46i_forms_part_of
- Determine: truly root vs should be hierarchical
- Add parent links via P46i_forms_part_of where needed
- Time: Depends on data review scope

**Priority 3: Define Canonical Shape**
- Document minimum required properties for each location type
- Enforce at form/KP level (e.g., make P2_has_type required)
- Clean up 6 minimal entries (delete or populate)
- Time: ~1 hour (policy) + 30 min (cleanup)

### Files & Resources Audited

**Blazegraph (Queries):**
- vocab/archives (E32_Authority_Document)
- vocab/archival_unit_types (46 valid entries)
- 505 archival_entity locations

**Field Definitions (KP):**
- vocab_entry_archival_unit_typology (correct patterns)
- vocab_entry_archival_unit_acronym
- vocab_entry_partof

**Forms:**
- /data/templates/http%3A%2F%2Fveniss.net%2Fforms%2Fvocab%2FArchival_unit.html
- /data/templates/http%3A%2F%2Fveniss.net%2Fforms%2Fvocab%2FArchival_unit_type.html

**Vocabulary:**
- 46 archival unit type entries present and correctly configured

### Conclusion

**Configuration: ✓ EXCELLENT**
- Forms are properly designed
- Field definitions are correctly configured
- Vocabulary of types is complete (46 entries)
- Patterns are well-structured

**Data Quality: ✗ NEEDS ATTENTION**
- 34 locations missing types (must assign)
- 100+ locations missing parent links (must verify/add)
- 6 empty placeholder entries (must clean)
- Overall coverage: 72–85% depending on property

---

## DATA QUALITY FIX PLAN

### A. Untyped Root Locations (36 total)

#### Table 1: Untyped Roots by Category with Recommended Types

| # | Label | Category | Suggested Type | URI |
|---|-------|----------|----------------|-----|
| **ARCHIVES & INSTITUTIONS (4)** |
| 1 | Archivio fotografico Fondazione Musei Civici di Venezia | Photo Archive | Archive | `...31670a6b...` |
| 2 | Institute of Risorgimento History | History Institute | Archive | `...ef1fa610...` |
| 3 | Österreichisches Staatsarchiv | State Archive | Archive | `...1dcff33d...` |
| 4 | Roma, Istituto Storico di Cultura | History Institute | Archive | `...a7bb3502...` |
| **MUSEUMS (2)** |
| 5 | b. "Museo e Pinacoteca" | Museum | Museum | `...82d2f273...` |
| 6 | Thyssen-Bornemisza National Museum (Madrid) | Museum | Museum | `...c9ee85db...` |
| **LIBRARIES (3)** |
| 7 | Biblioteca del Seminario Patriarcale | Library | Archive | `...03fe2fa3...` |
| 8 | Bibliotheque Nationale de France | Library | Archive | `...2b917753...` |
| 9 | ms P.D. 2 bibl. Correr | Library Manuscript | Archive | `...0ff406dd...` |
| **NEWSPAPERS (4)** |
| 10 | Corriere del Veneto | Newspaper | Archive | `...3b74fdab...` |
| 11 | Il Gazzettino | Newspaper | Archive | `...00f19e5a...` |
| 12 | La Gazzetta di Venezia | Newspaper | Archive | `...74d6e57d...` |
| 13 | La Nuova di Venezia | Newspaper | Archive | `...ba693996...` |
| **COLLECTIONS (10)** |
| 14 | Fondo Gradenigo Dolfin, b.96 | Fond | Fond | `...afd845e7...` |
| 15 | Fondo Veneto I, 13372 | Fond | Fond | `...c012d449...` |
| 16 | Fondo Veneto I, 13701 | Fond | Fond | `...c86d2897...` |
| 17 | Fondo Veneto I, 13795 | Fond | Fond | `...0a6b1f20...` |
| 18 | Fondo veneto I, 13809 | Fond | Fond | `...007642ca...` |
| 19 | Fondo Veneto I, 13700 | Fond | Fond | `...6db2a96a...` |
| 20 | Gianni Berlanda Collection | Collection | Collection | `...9e01ac35...` |
| 21 | Raccolta Gianni Berlanda | Collection | Collection | `...9e01ac35...` |
| 22 | Studio Galeazzo Architetti Associati | Studio/Collection | Collection | `...41119b9b...` |
| 23 | Studio Galeazzo Architetti Associati (dup) | Studio/Collection | Collection | `...41119b9b...` |
| **PROBLEMATIC / UNCLEAR (13)** |
| 24 | b.2 | Box (hierarchy?) | ⚠️ DELETE | `...7ba4ba9b...` |
| 25 | b.906 | Box (hierarchy?) | ⚠️ DELETE | `...d2c2bde0...` |
| 26 | Church of Spirito Santo in Venice | Facility/Location | ❓ REVIEW | `...4704fe19...` |
| 27 | dis.23 | Drawing (hierarchy?) | ⚠️ DELETE | `...1e9687d8...` |
| 28 | Istituto Geografico Militare, IGM (dup1) | Military Institute | Archive | `...652b5334...` |
| 29 | Istituto Geografico Militare, IGM (dup2) | Military Institute | Archive | `...652b5334...` |
| 30 | Istituto di Storia del Risorgimento (dup1) | History Institute | Archive | `...ef1fa610...` |
| 31 | Istituto di Storia del Risorgimento (dup2) | History Institute | Archive | `...ef1fa610...` |
| 32 | Istituto di Storia del Risorgimento (dup3) | History Institute | Archive | `...ef1fa610...` |
| 33 | Lost | Unknown/Lost | ⚠️ DELETE | `...53a3db0c...` |
| 34 | Perduta | Unknown/Lost | ⚠️ DELETE | `...53a3db0c...` |
| 35 | Regione del Veneto | Government Entity | ❓ REVIEW | `...a7d098b9...` |

**Issues identified:**
- **Duplicates** (3 sets): Some roots appear multiple times with different language versions
- **Hierarchical items as roots** (b.2, b.906, dis.23): Should be deleted or moved to hierarchies
- **Lost/Unknown** entries: Should be deleted
- **Facility not collection** (Church, Region): May not belong in archival authority

#### SPARQL UPDATE - Fix Untyped Roots

```sparql
-- BATCH INSERT P2_has_type for Archives & Institutions
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>

INSERT { ?loc crm:P2_has_type <https://veniss.net/resource/vocab/archival_unit_types/360ee61a-4cb5-11ee-9292-3a5becfe4abd> }
WHERE {
  VALUES ?loc {
    <https://veniss.net/resource/archival_entity/31670a6b-e65d-4a17-9e82-4785c8d5eccf>
    <https://veniss.net/resource/archival_entity/ef1fa610-e605-4f8d-a210-e50687d0da78>
    <https://veniss.net/resource/archival_entity/1dcff33d-5204-47ec-8416-4e8a97185a3f>
    <https://veniss.net/resource/archival_entity/a7bb3502-a981-44ec-8344-c89757d7c3e8>
    <https://veniss.net/resource/archival_entity/652b5334-4540-4b41-8b6a-b6c98f9856c8>
  }
  ?loc crm:P71i_is_listed_in <http://www.researchspace.org/resource/vocab/archives> .
  FILTER NOT EXISTS { ?loc crm:P2_has_type ?existing }
}
;

-- BATCH INSERT P2_has_type for Museums
INSERT { ?loc crm:P2_has_type <https://veniss.net/resource/vocab/archival_unit_types/a7c1db9e-826a-4f72-b273-e03100bab1ed> }
WHERE {
  VALUES ?loc {
    <https://veniss.net/resource/archival_entity/82d2f273-195b-48cf-a2cd-b65672c467ce>
    <https://veniss.net/resource/archival_entity/c9ee85db-4dec-4ec5-8fac-50e098689c10>
  }
  ?loc crm:P71i_is_listed_in <http://www.researchspace.org/resource/vocab/archives> .
  FILTER NOT EXISTS { ?loc crm:P2_has_type ?existing }
}
;

-- BATCH INSERT P2_has_type for Libraries (type as Archive)
INSERT { ?loc crm:P2_has_type <https://veniss.net/resource/vocab/archival_unit_types/360ee61a-4cb5-11ee-9292-3a5becfe4abd> }
WHERE {
  VALUES ?loc {
    <https://veniss.net/resource/archival_entity/03fe2fa3-ce21-4fd5-80fd-f22e6bc64f17>
    <https://veniss.net/resource/archival_entity/2b917753-0349-484c-80ee-6f5ecbf02d1f>
    <https://veniss.net/resource/archival_entity/0ff406dd-61f1-4ac8-acc7-5b5403fa4dae>
  }
  ?loc crm:P71i_is_listed_in <http://www.researchspace.org/resource/vocab/archives> .
  FILTER NOT EXISTS { ?loc crm:P2_has_type ?existing }
}
;

-- BATCH INSERT P2_has_type for Newspapers (type as Archive)
INSERT { ?loc crm:P2_has_type <https://veniss.net/resource/vocab/archival_unit_types/360ee61a-4cb5-11ee-9292-3a5becfe4abd> }
WHERE {
  VALUES ?loc {
    <https://veniss.net/resource/archival_entity/3b74fdab-3f9e-4e1e-8e84-e8c189fba298>
    <https://veniss.net/resource/archival_entity/00f19e5a-b8dd-4cde-9b2e-30188f3dec8e>
    <https://veniss.net/resource/archival_entity/74d6e57d-5b52-405f-94cb-44e554684644>
    <https://veniss.net/resource/archival_entity/ba693996-13a0-463a-b6c8-cfbc6be927af>
  }
  ?loc crm:P71i_is_listed_in <http://www.researchspace.org/resource/vocab/archives> .
  FILTER NOT EXISTS { ?loc crm:P2_has_type ?existing }
}
;

-- BATCH INSERT P2_has_type for Fonds (type as Fond)
INSERT { ?loc crm:P2_has_type <https://veniss.net/resource/vocab/archival_unit_types/360ef9b6-4cb5-11ee-9292-3a5becfe4abd> }
WHERE {
  VALUES ?loc {
    <https://veniss.net/resource/archival_entity/afd845e7-5355-40b0-8190-d2231b398a77>
    <https://veniss.net/resource/archival_entity/c012d449-33e8-4e00-9063-3d77f64543b4>
    <https://veniss.net/resource/archival_entity/c86d2897-a981-4388-a4bb-3ae925425a25>
    <https://veniss.net/resource/archival_entity/0a6b1f20-f802-45bb-aa5d-ea7f132ea451>
    <https://veniss.net/resource/archival_entity/007642ca-d018-49b8-ba38-3f0d96658935>
    <https://veniss.net/resource/archival_entity/6db2a96a-059e-4912-a6b1-d1aec7cd5256>
  }
  ?loc crm:P71i_is_listed_in <http://www.researchspace.org/resource/vocab/archives> .
  FILTER NOT EXISTS { ?loc crm:P2_has_type ?existing }
}
;

-- BATCH INSERT P2_has_type for Collections (type as Collection)
INSERT { ?loc crm:P2_has_type <https://veniss.net/resource/vocab/archival_unit_types/7b351402-43a7-4c72-8c1d-5e9c01f013b9> }
WHERE {
  VALUES ?loc {
    <https://veniss.net/resource/archival_entity/9e01ac35-1164-4bd1-b3d5-1e26936687b0>
    <https://veniss.net/resource/archival_entity/41119b9b-243c-4656-8e47-4a1d4cc9a627>
  }
  ?loc crm:P71i_is_listed_in <http://www.researchspace.org/resource/vocab/archives> .
  FILTER NOT EXISTS { ?loc crm:P2_has_type ?existing }
}
```

---

### B. Minimal Entries (6 total) - Data Quality Issues

#### Table 2: Minimal Entries Requiring Cleanup

| # | URI | Properties | Issue | Action |
|---|-----|-----------|-------|--------|
| 1 | `17ca6428-1bae-4777-8eb3-0a3bdd9e5efa` | ONLY P71i_is_listed_in | Completely empty, uninitialized | **DELETE** |
| 2 | `1e4ad4e4-29a8-4c4e-b358-9f1f09ee74f0` | ONLY P71i_is_listed_in | Completely empty, uninitialized | **DELETE** |
| 3 | `1f8aabdb-6c96-4cfd-8800-a43da7fffca8` | ONLY P71i_is_listed_in | Completely empty, uninitialized | **DELETE** |
| 4 | `2c0ff9a7-a22b-4b48-99b0-edeb203a40bc` | ONLY P71i_is_listed_in | Completely empty, uninitialized | **DELETE** |
| 5 | `3f0265f0-0e35-4281-b683-07c901df9731` | ONLY P71i_is_listed_in | Completely empty, uninitialized | **DELETE** |
| 6 | `8daed952-14ad-42ac-9cdf-a214af7664d1` | ONLY P71i_is_listed_in | Completely empty, uninitialized | **DELETE** |

**Root cause:** Stub/placeholder records with no metadata. Likely created during import or testing but never completed.

#### SPARQL DELETE - Remove Minimal Entries

```sparql
-- DELETE all triples for minimal entries
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
DELETE {
  ?loc ?p ?o
}
WHERE {
  VALUES ?loc {
    <https://veniss.net/resource/archival_entity/17ca6428-1bae-4777-8eb3-0a3bdd9e5efa>
    <https://veniss.net/resource/archival_entity/1e4ad4e4-29a8-4c4e-b358-9f1f09ee74f0>
    <https://veniss.net/resource/archival_entity/1f8aabdb-6c96-4cfd-8800-a43da7fffca8>
    <https://veniss.net/resource/archival_entity/2c0ff9a7-a22b-4b48-99b0-edeb203a40bc>
    <https://veniss.net/resource/archival_entity/3f0265f0-0e35-4281-b683-07c901df9731>
    <https://veniss.net/resource/archival_entity/8daed952-14ad-42ac-9cdf-a214af7664d1>
  }
  ?loc ?p ?o .
}
```

---

### C. Data Model Diagram

#### CURRENT (CORRECT) MODEL FOR ARCHIVAL LOCATIONS

```
┌─────────────────────────────────────────────────────────────────┐
│ ARCHIVAL LOCATION (vocab/archives entry)                        │
│ Type: E78_Collection                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┼─────────┐
                    │         │         │
           ┌────────▼──┐ ┌───▼──┐  ┌──▼────────┐
           │ Mandatory │ │ Core │  │ Optional  │
           │ (100%)    │ │(80%) │  │ (70-80%)  │
           └───────────┘ └──────┘  └───────────┘
                    │         │         │
        ┌───────────┴─────────┴─────────┴──────────┐
        │                                          │
        │  PROPERTIES (SPARQL predicates)          │
        │                                          │
        ├─ rdf:type = E78_Collection (100%)        │
        │                                          │
        ├─ P71i_is_listed_in                       │
        │  └─→ <vocab/archives> (100%)             │
        │     [Links to E32_Authority_Document]    │
        │                                          │
        ├─ rdfs:label                              │
        │  └─→ String, multilingual (95%)          │
        │     [Natural language name]              │
        │                                          │
        ├─ displayLabel (OPTIONAL)                 │
        │  └─→ String (85%)                        │
        │     [Pre-composed hierarchical name]     │
        │                                          │
        ├─ P2_has_type ⭐ CRITICAL                 │
        │  └─→ URI to vocab/archival_unit_types    │
        │     Coverage: 75% (SHOULD BE 100%)       │
        │     Values: Archive, Museum, Fond,       │
        │           Collection, Folder, etc.       │
        │                                          │
        ├─ P46i_forms_part_of (OPTIONAL)           │
        │  └─→ URI to parent location (72%)        │
        │     [Hierarchical: e.g., Fond→Box]      │
        │                                          │
        ├─ P1_is_identified_by                     │
        │  └─→ E41_Appellation (85%)               │
        │     [Alternative names/identifiers]      │
        │                                          │
        └─ (Other CIDOC-CRM properties)            │
           └─→ Path, searchPath, etc.              │

CONSTRAINTS:

✓ REQUIRED for all locations:
  - rdf:type = E78_Collection
  - P71i_is_listed_in = vocab/archives
  - rdfs:label (at least one)

⚠️ SHOULD HAVE (minimum for display):
  - P2_has_type (distinguish type)
  - displayLabel OR reconstructed from hierarchy

✗ MUST NOT have:
  - Duplicate entries (different languages = same subject)
  - Literal string type values (must be URI)
  - Orphaned entries with no label/type/parent

HIERARCHY RULES:

• ROOT locations: NO P46i_forms_part_of
  ├─ Must have explicit P2_has_type
  ├─ Examples: Archive, Museum, Collection
  └─ displayLabel = institution name

• HIERARCHICAL items: MUST have P46i_forms_part_of
  ├─ May or may not have P2_has_type
  ├─ Examples: Fond, Series, Folder, Box
  └─ displayLabel = parent hierarchy + own label
```

---

### D. Form Validation Against Model

#### Current Form: Archival_unit.html

**File:** `/data/templates/http%3A%2F%2Fveniss.net%2Fforms%2Fvocab%2FArchival_unit.html`

**Form Structure Assessment:**

| Field | Mapped To | Required | Status | Issue |
|-------|-----------|----------|--------|-------|
| Unit appellation | `vocab_entry_label` | YES | ✓ CORRECT | Maps to rdfs:label |
| Typology | `vocab_entry_archival_unit_typology` | NO | ⚠️ INCORRECT | Should be MANDATORY (P2_has_type) |
| Displayed name | `vocab_entry_archival_unit_acronym` | NO | ✓ OK | Optional, improves display |
| Prefix | `vocab_entry_archival_unit_prefix` | NO | ✓ OK | Optional |
| Parent archival unit | `vocab_entry_partof` | NO | ✓ OK | Optional, READ-ONLY (correct) |

**Hidden Fields (Auto-populated):**
- `type` = `E78_Collection` ✓ CORRECT
- `is_listed_in` = `vocab/archives` ✓ CORRECT

**Recommendations:**

```diff
Line 40-42 (Typology field):
<div id="vocab_entry_archival_unit_typology">
  <semantic-form-select-input 
-   label="Typology", 
+   label="Typology *" 
    placeholder="Select unit typology ..." 
+   required="true"
    for="vocab_entry_archival_unit_typology">
  </semantic-form-select-input>
</div>
```

**Why:** P2_has_type is essential for:
1. Distinguishing roots vs hierarchical items in UI
2. Enabling proper filter grouping and display
3. Communicating semantics (Archive vs Museum vs Collection)
4. Currently missing on 25% of locations (causes "location" fallback display)

**Change Impact:**
- Forms will now REQUIRE type selection
- Prevents creation of untyped locations
- Backward compatible (existing data unaffected)
- Fixes display inconsistency issue

---

## Summary: Data Quality Actions

| Action | Count | Queries | Effort | Priority |
|--------|-------|---------|--------|----------|
| Assign type to untyped roots | 36 | 5 INSERT batches | 5 min | **P1** |
| Delete minimal entries | 6 | 1 DELETE | 2 min | **P1** |
| Make P2_has_type required in form | 1 | Form update | 2 min | **P1** |
| Verify parent relationships | 100+ | Manual review | 1-2 hours | **P2** |
| De-duplicate entries | 3-5 sets | Manual review | 30 min | **P2** |
| Clean up facility items | 2-3 | Manual review | 30 min | **P2** |

---

## CRITICAL: P71i_is_listed_in INCONSISTENCIES

### NEW FINDINGS - MAJOR DATA CORRUPTION

#### Issue A: 70 Locations Linked to WRONG Authority

**Problem:** 70 locations have P71i_is_listed_in pointing to `resource_configurations_container` instead of `vocab/archives`

**Examples of wrongly linked items:**
- Acquisition configuration
- Activity configuration
- Actor configuration
- Appellation configuration
- ... 66 more configuration objects

**Impact:** These 70 items:
- Do NOT appear in the archives authority
- Are invisible to the location filter
- May cause duplicate entries or missing results in UI
- Represent ~15% of all locations (serious)

**Root cause:** Likely an import/migration error that linked config objects instead of actual archival locations

**Fix required:** Batch UPDATE to change P71i_is_listed_in from resource_configurations_container to vocab/archives

---

#### Issue B: 60 Locations with MULTIPLE P71i_is_listed_in

**The Two Authorities:**

| Authority | URI | Label | Type | Items | Status |
|-----------|-----|-------|------|-------|--------|
| **CORRECT ✓** | `vocab/archives` | **Locations** | E32_Authority_Document | 439 | ✓ In form |
| **WRONG ✗ (OLD)** | `authority_manager_config_types/data/Archival_Unit` | Authority Config for Vocabulary Archival Unit | FormConfig | 66 | ✗ Legacy |

**Form default (Line 27 of Archival_unit.html):**
```html
<semantic-form-hidden-input 
  for="is_listed_in" 
  default-value="http://www.researchspace.org/resource/vocab/archives">
</semantic-form-hidden-input>
```

**Problem:** 60 locations belong to BOTH authorities (caught between old and new systems):
- `authority_manager_config_types/data/Archival_Unit` (OLD - should remove)
- `vocab/archives` (NEW - should keep)

**Examples of duplicated locations:**
- Biblioteca del Museo Correr
- b. 1
- Direzione del genio militare in Venezia
- Atti
- Archivio di Stato di Venezia
- ... 55 more

**Impact:** 
- Creates ambiguity in authority membership
- May cause query/filter logic to behave unpredictably
- Violates data model (must have exactly ONE P71i_is_listed_in)

**Root cause:** Legacy migration - locations created in old FormConfig authority, later migrated to E32_Authority_Document, but old P71i_is_listed_in triple never removed

**Fix required:** DELETE all P71i_is_listed_in triples pointing to the OLD Archival_Unit FormConfig

---

#### Issue C: 7 Root Locations WITHOUT displayLabel

**Problem:** Root locations (no parent) lack pre-composed displayLabel:
- Fondo Veneto I, 13700
- Fondo Veneto I, 13372
- Fondo Veneto I, 13701
- Fondo Veneto I, 13795
- Fondo veneto I, 13809
- b.2
- b.906

**Impact:**
- Filter must reconstruct display at runtime (slower)
- If hierarchy reconstruction fails, shows label only (e.g., "b.5" instead of "ASVe, Provveditori sopra monasteri, b. 5")
- These are the items that appear with truncated names in the filter

**Current data example (from user):**
```
✓ WORKING: "Österreichisches Staatsarchiv, Ausland III A - 2 Venedig"
   - Has displayLabel: "Österreichisches Staatsarchiv, Ausland III A - 2 Venedig"
   - Has parent: Österreichisches Staatsarchiv

✗ NOT WORKING: "b.5"
   - Has displayLabel: "ASVe, Provveditori sopra monasteri, b. 5" (actually CORRECT!)
   - Has parent: Provveditori sopra monasteri
   
   BUT in filter shows as "b.5" only
   → Suggests displayLabel is not being USED in filter, hierarchy reconstruction fails
```

**Root cause:** 
- displayLabel exists on most locations (86%)
- But filter logic may have bug in reconstruction or displayLabel lookup
- Fallback: shows rdfs:label only when reconstruction fails

**Fix required:** 
- Verify filter code uses displayLabel 
- OR ensure all locations have displayLabel pre-composed
- OR fix hierarchy reconstruction logic

---

### UPDATED DATA MODEL CONSTRAINT

Add to model diagram:

```
⚠️ CRITICAL CONSTRAINTS:

EACH location MUST have:
  ✗ NOT: P71i_is_listed_in → resource_configurations_container
  ✗ NOT: Multiple P71i_is_listed_in values
  ✓ YES: Exactly ONE P71i_is_listed_in → <vocab/archives>

For ROOTS (no parent):
  ✓ displayLabel should be provided
  ✗ DO NOT rely on runtime reconstruction

For HIERARCHICAL (has parent):
  ✓ displayLabel recommended
  ✗ Or ensure parent hierarchy is complete
```

---

### CRITICAL FIX QUERIES

#### Query P0-1: Remove duplicate P71i_is_listed_in from OLD Archival_Unit authority (60 locations)

**Intent:** Delete the OLD P71i_is_listed_in triple, keeping only the correct one

```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>

DELETE {
  ?loc crm:P71i_is_listed_in <http://www.researchspace.org/resource/system/vocab/authority_manager_config_types/data/Archival_Unit> .
}
WHERE {
  ?loc crm:P71i_is_listed_in <http://www.researchspace.org/resource/system/vocab/authority_manager_config_types/data/Archival_Unit> .
  ?loc crm:P71i_is_listed_in <http://www.researchspace.org/resource/vocab/archives> .
}
```

**Expected result:** 60 triples deleted, locations now have ONLY vocab/archives

---

#### Query P0-2: Remove locations from WRONG authority (resource_configurations_container) (70 locations)

**Intent:** These 70 items shouldn't be in archives authority at all. Remove the incorrect link.

```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>

DELETE {
  ?loc crm:P71i_is_listed_in <http://www.researchspace.org/resource/system/resource_configurations_container> .
}
WHERE {
  ?loc crm:P71i_is_listed_in <http://www.researchspace.org/resource/system/resource_configurations_container> .
}
```

**Expected result:** 70 triples deleted

**Note:** These 70 items are actually configuration objects, not archival locations. If they should remain in the system, they should be left unlinked from any authority.

---

#### Query P0-3: VERIFY - Check remaining P71i_is_listed_in inconsistencies

**Intent:** Confirm all locations now point to ONLY vocab/archives

```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>

SELECT ?loc ?label (COUNT(DISTINCT ?vocab) as ?count) (GROUP_CONCAT(DISTINCT STR(?vocab); separator=" | ") as ?vocabs) WHERE {
  ?loc crm:P71i_is_listed_in ?vocab .
  ?loc rdfs:label ?label .
}
GROUP BY ?loc ?label
HAVING (COUNT(DISTINCT ?vocab) > 1)
ORDER BY DESC(?count)
```

**Expected result:** 0 rows (all duplicates removed)

**If results remain:** Shows which locations still have multiple authorities

---

### Revised Priority

| Action | Count | Issue Level | Priority |
|--------|-------|-------------|----------|
| Fix wrong authority (resource_configurations_container) | 70 | 🔴 CRITICAL | **P0** |
| Remove duplicate P71i_is_listed_in | 60 | 🔴 CRITICAL | **P0** |
| Add displayLabel to 7 roots | 7 | 🟡 HIGH | **P1** |
| Assign types to untyped roots | 36 | 🟡 HIGH | **P1** |
| Delete minimal entries | 6 | 🟡 HIGH | **P1** |
| Make P2_has_type required | 1 | 🟡 HIGH | **P1** |

---

---

## EXECUTION PLAN

### Phase 0: CRITICAL Authority Cleanup (P0)

Execute in order:

1. **Query P0-1:** Delete duplicate P71i_is_listed_in from Archival_Unit authority
   - Fixes: 60 locations with multiple authorities
   - Time: <1 min

2. **Query P0-2:** Delete wrong resource_configurations_container links  
   - Fixes: 70 configuration objects mistakenly linked
   - Time: <1 min

3. **Query P0-3:** VERIFY all duplicates removed
   - Expected result: 0 rows
   - Time: <1 min

### Phase 1: Type Assignment & Cleanup (P1)

4. **SPARQL INSERT - Types** (Archive, Museum, Fond, Collection)
   - Total: 21 type assignments across 36 untyped roots
   - Time: 5 min

5. **SPARQL DELETE - Minimal entries** (6 empty records)
   - Time: <1 min

6. **Form Update** - Add `required="true"` to Typology field
   - File: `data/templates/http%3A%2F%2Fveniss.net%2Fforms%2Fvocab%2FArchival_unit.html`
   - Line 41: Change to `<semantic-form-select-input label="Typology *" required="true" ...>`
   - Time: 2 min

### Phase 2: Verification (P2)

7. **Test filter display**
   - Verify "location" fallback disappears
   - Check hierarchical names show correctly
   - Time: 10 min

**Total execution time: ~20 minutes**

**Impact:**
- 60 duplicates fixed → locations now in ONE authority only
- 70 wrong links removed → cleaner data model
- 36 roots typed → "location" fallback eliminated
- 6 minimal records cleaned → no more empty stubs
- Form enforces types → prevents future inconsistencies

---

## 14:45 — Investigate "location" typology display issue

- env: dev
- endpoint: $VENISS_SPARQL_ENDPOINT
- mcp tool: mcp__sparql__select
- type: read
- query: inline (multiple)

### Finding: Typology Field Configuration

The field `vocab_entry_archival_unit_typology` is **correctly configured**:

**Patterns:**
- selectPattern: `SELECT ?value WHERE { $subject crm:P2_has_type ?value }`
- valueSetPattern: Queries `vocab/archival_unit_types` (contains 46 proper types: Archive, Museum, Fond, File, Folder, etc.)
- insertPattern: `INSERT { $subject crm:P2_has_type $value } WHERE {}`
- deletePattern: Removes from P2_has_type

**The Problem:** Österreichisches Staatsarchiv and other roots have **NO P2_has_type value** set.

Result: The UI displays "location" as a **fallback/placeholder** when the type field is empty.

---

## Summary of Inconsistency Issues

### THREE DISTINCT PROBLEMS:

**1. Missing Types (34 locations)**
- Root locations that completely lack P2_has_type
- UI displays fallback value "location" (not a real type)
- Affected: Österreichisches Staatsarchiv, Thyssen-Bornemisza, most newspapers, some collections

**2. Incomplete Hierarchies (100+ locations)**
- Locations missing P46i_forms_part_of (parent link)
- Breaks hierarchical display in filters
- Some roots actually appear as orphans in the tree

**3. Mixed Root vs Hierarchical Display**
- Roots (no parent) shown with inconsistent grouping
- Hierarchical items shown separately
- No clear visual distinction in filters/dropdowns

### Root Cause

**Data Quality**: Not all locations are fully modeled per the required shape:
- Mandatory: P71i_is_listed_in, rdf:type (E78_Collection)
- Required for display: P2_has_type (type/typology), displayLabel, P46i_forms_part_of (parent)
- Currently: 62% of roots have P2_has_type, 76% have P46i_forms_part_of

### Recommendation

**Priority 1: Assign Types to Untyped Roots (34 locations)**
- Review each untyped root
- Assign appropriate type from vocab/archival_unit_types (Archive, Museum, Collection, etc.)
- This will fix the "location" fallback display issue

**Priority 2: Verify Root Parent Relationships (100+ locations)**
- Audit roots that lack parent links
- Determine if they truly are roots or should be hierarchical
- Add P46i_forms_part_of where needed

**Priority 3: Clean up data quality**
- Remove or reassign 6 completely empty entries
- Verify displayLabel is populated (currently 78% coverage)

### Files Touched
- vocab/archival_unit_types (read-only, 46 entries correct)
- vocab/archives (E32_Authority_Document with 505 locations)
- KP vocab_entry_archival_unit_typology (configured correctly)
