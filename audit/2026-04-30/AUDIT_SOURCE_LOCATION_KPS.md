# Source_Primary Location KPs — Field Definition Audit
Session: 2026-04-30

Audit of the field definitions (KPs) referenced from the Location tab of [Source_Primary.html](../../data/templates/http%3A%2F%2Fveniss.net%2Fforms%2FSource_Primary.html). KPs are stored in the triplestore in named graphs `<KP-uri>/context`. Two data-quality issues were found and are documented here. A third (semantic modelling of the P53 chain) was deferred.

---

## 14:55 — Locate KP storage and dump patterns

- env: prod
- endpoint: `$VENISS_SPARQL_ENDPOINT` (https://veniss.net/sparql)
- tool: curl + SPARQL JSON / CSV
- type: read

```sparql
SELECT ?prop ?pat WHERE {
  GRAPH <https://veniss.net/container/fieldDefinitionContainer/{KP}/context> {
    <https://veniss.net/container/fieldDefinitionContainer/{KP}> ?prop ?bn .
    ?bn <http://spinrdf.org/sp#text> ?pat .
  }
}
```

- result: 9 KPs dumped (`source_location_switch`, `source_location_archival`, `source_location_current`, `source_location_carrier_name`, `source_location_carrier_type`, `source_forms_part_of_secondary_source`, `vocab_entry_archival_unit_acronym`, `vocab_entry_archival_unit_prefix`, `source_typology`).
- notes: select / insert / delete patterns are blank-node references with `sp:text` carrying the SPARQL string; `valueSetPattern` likewise.

---

## Issue 1 — `source_location_carrier_name` has malformed `field:domain`

### Observed

KP `https://veniss.net/container/fieldDefinitionContainer/source_location_carrier_name`:

| Property | Value |
|---|---|
| `field:domain` | **`crm:E78`** ❌ |
| `field:xsdDatatype` | `xsd:string` ✓ |
| `field:maxOccurs` | 1 ✓ |
| `field:selectPattern` | reads `crm:E42_Identifier` linked via `P1_is_identified_by` with `P2_has_type <vocab/information_carrier/name>` ✓ |
| `field:insertPattern` | mints `<subject>/information_carrier_name` as the E42 ✓ |

`crm:E78` is **not a valid CIDOC-CRM class** — the class is `crm:E78_Collection`. This is almost certainly a typo, not an intentional namespace.

### Verification

```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
SELECT (COUNT(DISTINCT ?subj) as ?n) WHERE {
  ?subj crm:P1_is_identified_by ?id .
  ?id crm:P2_has_type <https://veniss.net/resource/vocab/information_carrier/name>
}
```

- result: **440 location nodes** carry an information-carrier name today (subjects are URIs of shape `.../source/{uuid}/location`).
- notes: subjects are the composite-location nodes which carry `rdf:type = crm:E78_Collection`. So the *intended* domain is `E78_Collection`.

### Impact

- Field-definition validators that check `domain` against the form's `type` hidden input will fail to match — current input sets `type = crm:E78_Collection` (Source_Primary.html L293/L372), but KP says `crm:E78`.
- May silently fall back to permissive behaviour today; would break stricter form-validation tooling later.
- Cosmetic, but misleading for anyone reading the KP.

### Fix

```sparql
PREFIX field: <http://www.researchspace.org/resource/system/fields/>
WITH <https://veniss.net/container/fieldDefinitionContainer/source_location_carrier_name/context>
DELETE { <https://veniss.net/container/fieldDefinitionContainer/source_location_carrier_name>
         field:domain <http://www.cidoc-crm.org/cidoc-crm/E78> }
INSERT { <https://veniss.net/container/fieldDefinitionContainer/source_location_carrier_name>
         field:domain <http://www.cidoc-crm.org/cidoc-crm/E78_Collection> }
WHERE  { <https://veniss.net/container/fieldDefinitionContainer/source_location_carrier_name>
         field:domain <http://www.cidoc-crm.org/cidoc-crm/E78> }
```

- effort: <1 min, single triple
- risk: none — domain is metadata, no form behaviour depends on it at runtime
- rollback: trivial (reverse the DELETE/INSERT)

### Verification after fix

```sparql
SELECT ?o WHERE {
  GRAPH <https://veniss.net/container/fieldDefinitionContainer/source_location_carrier_name/context> {
    <https://veniss.net/container/fieldDefinitionContainer/source_location_carrier_name>
      <http://www.researchspace.org/resource/system/fields/domain> ?o
  }
}
```
- expected: `crm:E78_Collection` only.

---

## Issue 2 — `source_location_carrier_type.valueSetPattern` hard-codes Italian

### Observed

KP `source_location_carrier_type` `valueSetPattern`:

```sparql
SELECT ?value ?label WHERE {
  ?value crm:P71i_is_listed_in <https://veniss.net/resource/vocab/archival_unit_types> ;
         skos:broader <https://veniss.net/resource/vocab/archival_unit_types/360fd62e-4cb5-11ee-9292-3a5becfe4abd> ;
         rdfs:label ?label
  FILTER(LANG(?label) = "it")
}
```

The hard `LANG = "it"` filter means a non-Italian label that exists for the same value is invisible to this dropdown. If a future term is created with only an English label (or no language tag), it disappears from the picker.

### Verification

```sparql
SELECT ?lang (COUNT(*) as ?n) WHERE {
  ?value <http://www.cidoc-crm.org/cidoc-crm/P71i_is_listed_in> <https://veniss.net/resource/vocab/archival_unit_types> ;
         <http://www.w3.org/2004/02/skos/core#broader>
           <https://veniss.net/resource/vocab/archival_unit_types/360fd62e-4cb5-11ee-9292-3a5becfe4abd> ;
         <http://www.w3.org/2000/01/rdf-schema#label> ?label .
  BIND(LANG(?label) as ?lang)
} GROUP BY ?lang
```

| lang | n |
|---|---|
| en | 8 |
| it | 8 |

- result: today every term has both EN and IT labels, so the dropdown still shows 8 entries — no production breakage.
- notes: nevertheless any term added with only EN (or only `""`-tagged) will be silently hidden. Behaviour is also user-hostile for non-Italian editors who'd see Italian strings.

### Impact

- Silent omission risk for new vocab entries created via [Archival_unit_type.html](../../data/templates/http%3A%2F%2Fveniss.net%2Fforms%2Fvocab%2FArchival_unit_type.html) — that form accepts `["it", "en"]` (L26) but does not require both.
- Mixed-language UX: the rest of the form respects browser locale, this dropdown does not.
- Comparable KPs (`source_typology`, `source_location_archival/current` tree-pattern queries) use `(rso:displayLabel|rdfs:label|skos:prefLabel)` chains without a language filter — this KP is the outlier.

### Fix

Replace the `valueSetPattern` so a single label per value is returned, preferring user locale (or simply showing whatever label exists). Two viable options:

**Option A — drop the filter (show whichever label exists, may duplicate values):**

```sparql
SELECT ?value ?label WHERE {
  ?value crm:P71i_is_listed_in <https://veniss.net/resource/vocab/archival_unit_types> ;
         skos:broader <https://veniss.net/resource/vocab/archival_unit_types/360fd62e-4cb5-11ee-9292-3a5becfe4abd> ;
         rdfs:label ?label
}
```

**Option B — prefer EN, fall back to IT, fall back to any (recommended):**

```sparql
SELECT ?value (SAMPLE(?best) as ?label) WHERE {
  ?value crm:P71i_is_listed_in <https://veniss.net/resource/vocab/archival_unit_types> ;
         skos:broader <https://veniss.net/resource/vocab/archival_unit_types/360fd62e-4cb5-11ee-9292-3a5becfe4abd> ;
         rdfs:label ?label .
  BIND(IF(LANG(?label)="en", 1, IF(LANG(?label)="it", 2, 3)) as ?rank)
  {
    SELECT ?value (MIN(?rank) as ?minRank) WHERE {
      ?value rdfs:label ?l . BIND(IF(LANG(?l)="en", 1, IF(LANG(?l)="it", 2, 3)) as ?rank)
    } GROUP BY ?value
  }
  FILTER(?rank = ?minRank)
  BIND(?label as ?best)
} GROUP BY ?value
```

Recommended: **Option B** for stable single-row-per-value output and locale-aware preference. Patch via UPDATE on the blank-node `sp:text` triple in graph `<.../source_location_carrier_type/context>`.

```sparql
PREFIX field: <http://www.researchspace.org/resource/system/fields/>
PREFIX sp: <http://spinrdf.org/sp#>

WITH <https://veniss.net/container/fieldDefinitionContainer/source_location_carrier_type/context>
DELETE { ?bn sp:text ?old }
INSERT { ?bn sp:text """<NEW QUERY>""" }
WHERE  {
  <https://veniss.net/container/fieldDefinitionContainer/source_location_carrier_type>
    field:valueSetPattern ?bn .
  ?bn sp:text ?old .
}
```

- effort: 5 min (write + verify)
- risk: low — only affects the carrier-type dropdown rendering, no stored data touched
- rollback: re-run the same UPDATE with the original IT-only string

### Verification after fix

```sparql
PREFIX sp: <http://spinrdf.org/sp#>
SELECT ?text WHERE {
  GRAPH <https://veniss.net/container/fieldDefinitionContainer/source_location_carrier_type/context> {
    <https://veniss.net/container/fieldDefinitionContainer/source_location_carrier_type>
      <http://www.researchspace.org/resource/system/fields/valueSetPattern> ?bn .
    ?bn sp:text ?text .
  }
}
```

Then in the UI, open a Source_Primary "Archival Location" composite and confirm "Information Carrier type" dropdown shows all 8 entries with locale-appropriate labels.

---

## Summary

| # | KP | Property | Issue | Fix effort | Risk |
|---|---|---|---|---|---|
| 1 | `source_location_carrier_name` | `field:domain` | `crm:E78` (typo) → should be `crm:E78_Collection` | <1 min | none |
| 2 | `source_location_carrier_type` | `field:valueSetPattern` | hard-coded `LANG="it"` filter — silently hides non-IT vocab entries | 5 min | low |

Both fixes are metadata-only on KP definitions; no migration of source data is involved. Apply with SPARQL UPDATE against the named graphs `<KP-uri>/context`.

### Out of scope
- Semantic question of whether `source_location_archival` / `source_location_current` should use `P46i_forms_part_of` instead of duplicating `P53_has_former_or_current_location`. This would be a model change affecting 856 stored rows and is **deferred**.

### Files & Resources
- Forms: [Source_Primary.html](../../data/templates/http%3A%2F%2Fveniss.net%2Fforms%2FSource_Primary.html), [Archival_unit_type.html](../../data/templates/http%3A%2F%2Fveniss.net%2Fforms%2Fvocab%2FArchival_unit_type.html)
- KPs: in named graphs `https://veniss.net/container/fieldDefinitionContainer/{name}/context`
- Vocab: `https://veniss.net/resource/vocab/archival_unit_types` (carrier-type subtree under concept `360fd62e-4cb5-11ee-9292-3a5becfe4abd`)
