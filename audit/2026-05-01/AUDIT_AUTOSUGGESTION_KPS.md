# Autosuggestion KP Issues — `source_location_current` & `source_forms_part_of_secondary_source`
Session: 2026-05-01

User report: in `Source_Primary` form, the autocomplete for **Current Location** searches the entire graph (no scope), and the autocomplete for **Secondary Source** returns no results.

Audit of the two field definitions (KPs) backing those autocompletes. Both have problems; both fixable with single SPARQL UPDATEs.

---

## Setup

- env: prod
- endpoint: `$VENISS_SPARQL_ENDPOINT` (https://veniss.net/sparql)
- tool: curl + SPARQL JSON
- type: read

Pattern dump for each KP:
```sparql
PREFIX sp: <http://spinrdf.org/sp#>
PREFIX field: <http://www.researchspace.org/resource/system/fields/>
SELECT ?patternType ?text WHERE {
  <KP-IRI> ?patternType ?bnode .
  ?bnode sp:text ?text .
}
```

---

## Issue 1 — `source_location_current` has no `autosuggestionPattern`

### Current state of KP `<https://veniss.net/container/fieldDefinitionContainer/source_location_current>`

```sparql
# selectPattern (only retrieves already-bound value, does NOT scope autocomplete)
SELECT ?value ?label WHERE { $subject crm:P53_has_former_or_current_location $value }

# insertPattern
INSERT { $subject crm:P53_has_former_or_current_location $value } WHERE {}

# deletePattern
DELETE { $subject crm:P53_has_former_or_current_location $value }
WHERE  { $subject crm:P53_has_former_or_current_location $value }
```

**Missing:** `field:autosuggestionPattern` and `field:valueSetPattern`.

Without an autosuggestionPattern, ResearchSpace's autocomplete falls back to a generic graph-wide label match — searching every IRI in the dataset, which is what the user observes.

### What should be the scope of current locations?

User clarification: **NOT children of archives** (i.e., NOT items with `P2_has_type <…/archival_unit_types/360ee61a…>`)

**Instead:** the **root archival entities themselves** in `vocab/archives` — the institutions/collections at the top level (e.g., "Archivio di Stato di Venezia", "Biblioteca Nazionale Marciana", etc.). Plus Islands.

These are items where `crm:P71i_is_listed_in <http://www.researchspace.org/resource/vocab/archives>` AND they have no parent (i.e., NOT reachable by `crm:P46i_forms_part_of` from the query subject). In practice, roots are distinguishable by absence of `P46i_forms_part_of` or by explicit type flag.

### Dirty data note

58 `P53_Place` and 2 `E41_Appellation` in P53 links — flag for separate cleanup. Do not include in scope.

### Fix — add `autosuggestionPattern` + `valueSetPattern` constraining to root archives ∪ islands

Need BOTH patterns so the form's tree-picker works correctly (for both autocomplete AND dropdown scope).

```sparql
PREFIX field: <http://www.researchspace.org/resource/system/fields/>
PREFIX sp:    <http://spinrdf.org/sp#>

INSERT {
  <https://veniss.net/container/fieldDefinitionContainer/source_location_current>
    field:autosuggestionPattern [
      sp:text """SELECT DISTINCT ?value ?label WHERE {
  {
    ?value crm:P71i_is_listed_in <http://www.researchspace.org/resource/vocab/archives> .
    MINUS { ?value crm:P46i_forms_part_of ?parent . }
  }
  UNION
  { ?value a <https://veniss.net/ontology#Island> }
  ?value rdfs:label ?label .
  FILTER REGEX(STR(?label), \"?token\", \"i\")
} ORDER BY ASC(?label) LIMIT 10"""
    ] ;
    field:valueSetPattern [
      sp:text """SELECT DISTINCT ?value ?label WHERE {
  {
    ?value crm:P71i_is_listed_in <http://www.researchspace.org/resource/vocab/archives> .
    MINUS { ?value crm:P46i_forms_part_of ?parent . }
  }
  UNION
  { ?value a <https://veniss.net/ontology#Island> }
  ?value rdfs:label ?label .
} ORDER BY ASC(?label)"""
    ] .
}
WHERE {}
```

**Pattern explanation:**
- `crm:P71i_is_listed_in <…/vocab/archives>` — item is in the archives authority
- `MINUS { ?value crm:P46i_forms_part_of ?parent . }` — item has no parent → **root only**
- Union with `Island` type for completeness
- Autocomplete filters by token; valueSet returns all for tree-picker

**Note on label:** roots have `rdfs:label` = short name (e.g., "ASVe", "Biblioteca Marciana"). That is what the autocomplete/tree will display.

### Verification

After update, in the form, type "ven" in the Current Location autocomplete:
- Before: matches any IRI with "ven" in any label (whole graph)
- After: returns only **root** archival entities (institutions without parents) in `vocab/archives` and Islands matching "ven" (e.g., "Archivio di Stato di Venezia")

---

## Issue 2 — `source_forms_part_of_secondary_source` autocomplete returns nothing

### Current state of KP `<https://veniss.net/container/fieldDefinitionContainer/source_forms_part_of_secondary_source>`

```sparql
# autosuggestionPattern (broken)
SELECT ?value ?label WHERE {
  ?value a veniss_ontology:Source_Secondary ;
    rdfs:label|crm:P190_has_symbolic_content ?label .
  FILTER REGEX(STR(?label), "?token", "i")
} LIMIT 10
```

### Root cause: wrong label source + undefined prefix

1. **Prefix issue** — `veniss_ontology:` is not auto-resolved by RS at runtime.
2. **Label issue** — the label to search should NOT be `rdfs:label|crm:P190_has_symbolic_content` on the Source_Secondary itself. Instead, it's **computed at runtime** from the identified-by chain:
   - `$subject a Source_Secondary`
   - `$subject crm:P1_is_identified_by ?bibitem_identifier`
   - `?bibitem_identifier a crm:E41_Appellation`
   - `?bibitem_identifier crm:P2_has_type <https://veniss.net/resource/type/title>`
   - **label = `?bibitem_identifier rdfs:label`** (the title)

This is the title of the secondary source (e.g., "Carraro, Silvia, La laguna delle donne. Il monachesimo femminile a Venezia tra I…").

### Confirmation — query with correct pattern and full IRI

```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?value ?label WHERE {
  ?value a <https://veniss.net/ontology#Source_Secondary> ;
    crm:P1_is_identified_by ?bibitem_identifier .
  ?bibitem_identifier a crm:E41_Appellation ;
    crm:P2_has_type <https://veniss.net/resource/type/title> ;
    rdfs:label ?label .
  FILTER REGEX(STR(?label), "ven", "i")
} ORDER BY ASC(?label) LIMIT 10
```

→ 5+ results (titles containing "ven"). Pattern is now correct **and** scoped to the right label source.

129 instances of `<https://veniss.net/ontology#Source_Secondary>` exist; expect 100+ with title appellations.

### Fix — replace `autosuggestionPattern` with correct label extraction + full IRI

```sparql
PREFIX field: <http://www.researchspace.org/resource/system/fields/>
PREFIX sp:    <http://spinrdf.org/sp#>

DELETE {
  <https://veniss.net/container/fieldDefinitionContainer/source_forms_part_of_secondary_source>
    field:autosuggestionPattern ?old .
  ?old ?p ?o .
}
INSERT {
  <https://veniss.net/container/fieldDefinitionContainer/source_forms_part_of_secondary_source>
    field:autosuggestionPattern [
      sp:text """SELECT ?value ?label WHERE {
  ?value a <https://veniss.net/ontology#Source_Secondary> ;
    crm:P1_is_identified_by ?bibitem_identifier .
  ?bibitem_identifier a crm:E41_Appellation ;
    crm:P2_has_type <https://veniss.net/resource/type/title> ;
    rdfs:label ?label .
  FILTER REGEX(STR(?label), \"?token\", \"i\")
} ORDER BY ASC(?label) LIMIT 10"""
    ] .
}
WHERE {
  <https://veniss.net/container/fieldDefinitionContainer/source_forms_part_of_secondary_source>
    field:autosuggestionPattern ?old .
  ?old ?p ?o .
}
```

### Verification

After update, in the form, type "ven" in the Secondary Source autocomplete:
- Before: 0 results (broken prefix + wrong label source)
- After: ≥5 results (secondary source titles containing "ven")

---

## Dirty data tracking

- **P53 location links:** 58× `P53_Place` (property URI, not class) and 2× `E41_Appellation` found in `crm:P53_has_former_or_current_location` object position. These are errors — correct type should be `E78_Collection` or `Island`. **Action:** run separate cleanup query to find and remove these triples. Do not block the fixes above.

---

## Open questions (resolved)

1. ~~Scope of `source_location_current`~~ → **Resolved:** root archives only (no parent via `P46i_forms_part_of`), plus Islands.
2. ~~Label source for `source_forms_part_of_secondary_source`~~ → **Resolved:** extract from `P1_is_identified_by` appellation with `P2_has_type = title`, not simple `rdfs:label`.
3. **Path display in Current Location tree-picker:** dropdown will show short `rdfs:label` of roots (e.g., "ASVe"). If hierarchical paths are wanted for these roots, override `valueSetPattern` with the 8-level walk from `AUDIT_DISPLAYLABEL_RUNTIME` — but that's a separate enhancement (lower priority).

---

## Execution order

1. ✅ READ — patterns inspected, types audited, label sources clarified (above).
2. ⏳ WRITE — apply Fix 2 (`source_forms_part_of_secondary_source`). Lowest risk; restores broken feature with correct label extraction.
3. ⏳ WRITE — apply Fix 1 (`source_location_current`). Adds both `autosuggestionPattern` and `valueSetPattern` scoped to root archives ∪ islands.
4. ⏳ UI verify both autocompletes with sample tokens ("ven", "san", etc.).
5. ⏳ SEPARATE — Query and cleanup P53 dirty data (58× `P53_Place`, 2× `E41_Appellation` in location links).

---

## Files & Resources

| Resource | IRI |
|----------|-----|
| Source_Primary form | `data/templates/http%3A%2F%2Fveniss.net%2Fforms%2FSource_Primary.html` |
| Current location KP | `https://veniss.net/container/fieldDefinitionContainer/source_location_current` |
| Secondary source KP | `https://veniss.net/container/fieldDefinitionContainer/source_forms_part_of_secondary_source` |
| Source_Secondary class | `https://veniss.net/ontology#Source_Secondary` (129 instances) |
| Island class | `https://veniss.net/ontology#Island` |
| Archives authority | `http://www.researchspace.org/resource/vocab/archives` |

---

## Appendix — P53 Dirty Data Cleanup

### Audit query — find bad location links

```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
SELECT ?subject ?bad_value ?type WHERE {
  ?subject crm:P53_has_former_or_current_location ?bad_value .
  ?bad_value a ?type .
  FILTER(?type IN (<http://www.cidoc-crm.org/P53_Place>, <http://www.w3.org/2004/02/skos/core#Concept>, <http://www.cidoc-crm.org/cidoc-crm/E41_Appellation>))
}
```

Expected: 60 results (58 `P53_Place` + 2 `E41_Appellation`).

### Cleanup — delete bad P53 links

```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
DELETE { ?subject crm:P53_has_former_or_current_location ?bad_value . }
WHERE {
  ?subject crm:P53_has_former_or_current_location ?bad_value .
  ?bad_value a ?type .
  FILTER(?type IN (<http://www.cidoc-crm.org/P53_Place>, <http://www.cidoc-crm.org/cidoc-crm/E41_Appellation>))
}
```

**Note:** do NOT delete `Concept` — that may be a valid vocabulary item wrongly used as a location. First inspect.

**Status:** ⏳ Separate task — non-blocking for KP fixes.

---

## Implementation — Ready-to-Fire SPARQL UPDATEs

### Deploy Fix 1 — `source_location_current` (add auto + valueset patterns)

Copy-paste to Blazegraph:

```sparql
PREFIX field: <http://www.researchspace.org/resource/system/fields/>
PREFIX sp:    <http://spinrdf.org/sp#>
PREFIX crm:   <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>

INSERT {
  <https://veniss.net/container/fieldDefinitionContainer/source_location_current>
    field:autosuggestionPattern [
      sp:text """SELECT DISTINCT ?value ?label WHERE {
  {
    ?value crm:P71i_is_listed_in <http://www.researchspace.org/resource/vocab/archives> .
    MINUS { ?value crm:P46i_forms_part_of ?parent . }
  }
  UNION
  { ?value a <https://veniss.net/ontology#Island> }
  ?value rdfs:label ?label .
  FILTER REGEX(STR(?label), \"?token\", \"i\")
} ORDER BY ASC(?label) LIMIT 10"""
    ] ;
    field:valueSetPattern [
      sp:text """SELECT DISTINCT ?value ?label WHERE {
  {
    ?value crm:P71i_is_listed_in <http://www.researchspace.org/resource/vocab/archives> .
    MINUS { ?value crm:P46i_forms_part_of ?parent . }
  }
  UNION
  { ?value a <https://veniss.net/ontology#Island> }
  ?value rdfs:label ?label .
} ORDER BY ASC(?label)"""
    ] .
}
WHERE {}
```

### Deploy Fix 2 — `source_forms_part_of_secondary_source` (fix autosuggestion with correct label source)

Copy-paste to Blazegraph:

```sparql
PREFIX field: <http://www.researchspace.org/resource/system/fields/>
PREFIX sp:    <http://spinrdf.org/sp#>
PREFIX crm:   <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>

DELETE {
  <https://veniss.net/container/fieldDefinitionContainer/source_forms_part_of_secondary_source>
    field:autosuggestionPattern ?old .
  ?old ?p ?o .
}
INSERT {
  <https://veniss.net/container/fieldDefinitionContainer/source_forms_part_of_secondary_source>
    field:autosuggestionPattern [
      sp:text """SELECT ?value ?label WHERE {
  ?value a <https://veniss.net/ontology#Source_Secondary> ;
    crm:P1_is_identified_by ?bibitem_identifier .
  ?bibitem_identifier a crm:E41_Appellation ;
    crm:P2_has_type <https://veniss.net/resource/type/title> ;
    rdfs:label ?label .
  FILTER REGEX(STR(?label), \"?token\", \"i\")
} ORDER BY ASC(?label) LIMIT 10"""
    ] .
}
WHERE {
  <https://veniss.net/container/fieldDefinitionContainer/source_forms_part_of_secondary_source>
    field:autosuggestionPattern ?old .
  ?old ?p ?o .
}
```

---

## Verification Checklist

After both UPDATEs fire:

- [ ] No SPARQL errors in Blazegraph console
- [ ] In Source_Primary form, Current Location field: type "ven" → returns 3+ root archives (e.g., "Archivio di Stato di Venezia")
- [ ] In Source_Primary form, Secondary Source field: type "ven" → returns 5+ source titles (e.g., "Mazzucco, Gabriele, La presenza di San Secondo a Venezia …")
- [ ] Current Location tree-picker still displays all roots + islands in dropdown (not just token matches)
- [ ] No regression in other Source_Primary form fields
