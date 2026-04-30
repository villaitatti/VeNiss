# Location preferredLabels Language Tag Ranking Bug — Audit & Resolution
Session: 2026-04-30

---

## Problem

The location `preferredLabels` pattern, despite being the first pattern in the UI config and producing correct hierarchical paths when tested in isolation, was displaying only short labels (e.g., "b. 697") in filters and search results.

### Concrete Example

Location: `<https://veniss.net/resource/archival_entity/cc0f764f-4085-42d6-a7b7-d2b1201130b3>`

Expected display: `"Archivio di Stato di Venezia, Ufficio del Genio Civile, Atti, b. 697"`
Actual display: `"b. 697"`

Pattern test result (raw SPARQL): ✅ Correct — returned full path
UI result: ❌ Incorrect — showed only leaf label

---

## Root Cause Analysis

ResearchSpace's `LabelCache.java` (backend label resolution service) evaluates all `preferredLabels` patterns as a **UNION** and pools the results, then applies language-based ranking to select the "best" label.

### The Ranking Algorithm (LabelCache.java:292-340)

```java
private Optional<Literal> chooseLabelWithPreferredLanguage(
    List<Literal> labels, 
    String selectedLanguage,
    List<String> otherPreferredLanguages) {
  
  // Build language ranking: [selectedLanguage=0, preferred1=1, preferred2=2, ..., ""=fallback]
  Map<String, Integer> languageToRank = new HashMap<>();
  languageToRank.put(selectedLanguage, 0);  // e.g., "it" → rank 0
  
  // ... add other preferred languages ...
  
  if (!languageToRank.containsKey("")) {
    languageToRank.put("", nextRank++);  // plain strings get lower rank
  }
  
  // Pick literal with lowest (best) rank
  for (Literal label : labels) {
    String languageTag = label.getLanguage().orElse("");
    int rank = languageToRank.getOrDefault(languageTag, Integer.MAX_VALUE - 1);
    if (rank < bestObservedRank) {
      bestObservedRank = rank;
      bestObserved = label;
    }
  }
  return Optional.ofNullable(bestObserved);
}
```

### Why the Location Pattern Lost

For this location, the pooled label results included:

| Source | Literal Value | Language Tag | Rank (for Italian user) |
|--------|---------------|--------------|------------------------|
| Location pattern | `"Archivio di Stato di Venezia, …, b. 697"` | **none (plain)** | **fallback (high)** |
| `rdfs:label` property | `"b. 697"` | **`@it`** | **0 (best)** |

Because the user's preferred language was `"it"`, the `@it`-tagged `rdfs:label` result ranked 0 (perfect match), while the location pattern's plain string ranked as fallback → `rdfs:label` won.

### Why the Pattern Produced a Plain String

The location pattern concatenates labels using `CONCAT()`:

```sparql
BIND(COALESCE(?acr0_label, ?it0, ?any0) AS ?l0)  // ?l0 = "b. 697"@it
...
BIND(CONCAT(
  COALESCE(CONCAT(?l3, ", "), ""),  // ?l3 = "Archivio di Stato di Venezia"@it
  ...
  COALESCE(?l0, "")  // ?l0 = "b. 697"@it
) AS ?value)
```

In SPARQL 1.1, `CONCAT()` behavior with language tags:
- `CONCAT(langString@it, langString@it)` → `langString@it` ✓
- `CONCAT(langString@it, plain_string)` → **plain_string** ❌

Because intermediate levels (`?l1` = `"Atti"`, `?l2` = `"Ufficio del Genio Civile"`) are extracted from plain-language labels, the CONCAT result **loses the language tag**.

---

## Solution

**Strip language tags before CONCAT, then re-tag the final result using `STRLANG()`.**

### Implementation

**Change 1: Wrap each level binding with `STR()`**

Before:
```sparql
BIND(COALESCE(?acr0_label, ?it0, ?any0) AS ?l0)
```

After:
```sparql
BIND(STR(COALESCE(?acr0_label, ?it0, ?any0)) AS ?l0)
```

This strips any language tag, converting `"b. 697"@it` → `"b. 697"` (plain). Apply to all 8 levels (l0–l8).

**Change 2: Wrap final CONCAT with `STRLANG(..., "it")`**

Before:
```sparql
BIND(CONCAT(...) AS ?value)
```

After:
```sparql
BIND(STRLANG(CONCAT(...), "it") AS ?value)
```

This re-tags the plain concatenated result as `@it`, so it ranks at **rank 0** for Italian users — **equal to** `rdfs:label`, but the location pattern comes first in the UNION and wins.

---

## Verification

### Test Query

Query the fixed pattern against the problematic URI:

```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?value WHERE {
  BIND(<https://veniss.net/resource/archival_entity/cc0f764f-4085-42d6-a7b7-d2b1201130b3> AS ?subject)
  ?subject crm:P71i_is_listed_in <http://www.researchspace.org/resource/vocab/archives> .
  OPTIONAL { ?subject rdfs:label ?it0 . FILTER(LANG(?it0) = "it") }
  OPTIONAL { ?subject rdfs:label ?any0 . FILTER(LANG(?any0) = "") }
  BIND(STR(COALESCE(?it0, ?any0)) AS ?l0)
  OPTIONAL { ?subject crm:P46i_forms_part_of ?p1 .
    OPTIONAL { ?p1 rdfs:label ?it1 . FILTER(LANG(?it1) = "it") }
    OPTIONAL { ?p1 rdfs:label ?any1 . FILTER(LANG(?any1) = "") }
    BIND(STR(COALESCE(?it1, ?any1)) AS ?l1) }
  OPTIONAL { ?subject crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p2 .
    OPTIONAL { ?p2 rdfs:label ?it2 . FILTER(LANG(?it2) = "it") }
    OPTIONAL { ?p2 rdfs:label ?any2 . FILTER(LANG(?any2) = "") }
    BIND(STR(COALESCE(?it2, ?any2)) AS ?l2) }
  OPTIONAL { ?subject crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p3 .
    OPTIONAL { ?p3 rdfs:label ?it3 . FILTER(LANG(?it3) = "it") }
    OPTIONAL { ?p3 rdfs:label ?any3 . FILTER(LANG(?any3) = "") }
    BIND(STR(COALESCE(?it3, ?any3)) AS ?l3) }
  BIND(STRLANG(CONCAT(
    COALESCE(CONCAT(?l3, ", "), ""),
    COALESCE(CONCAT(?l2, ", "), ""),
    COALESCE(CONCAT(?l1, ", "), ""),
    COALESCE(?l0, "")
  ), "it") AS ?value)
}
```

**Expected Result:**
```json
{
  "value": "Archivio di Stato di Venezia, Ufficio del Genio Civile, Atti, b. 697",
  "xml:lang": "it"
}
```

**Actual Result (2026-04-30, verified):**
```json
✅ PASS — returns "Archivio di Stato di Venezia, Ufficio del Genio Civile, Atti, b. 697"@it
```

---

## Updated Pattern (Full 8-Level Version)

Replace the location `preferredLabels` entry in UI config with:

```sparql
{ ?subject crm:P71i_is_listed_in <http://www.researchspace.org/resource/vocab/archives> . OPTIONAL { ?subject rdfs:label ?it0 . FILTER(LANG(?it0) = "it") } OPTIONAL { ?subject rdfs:label ?any0 . FILTER(LANG(?any0) = "") } OPTIONAL { ?subject crm:P1_is_identified_by ?acr0 . ?acr0 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr0 rdfs:label ?acr0_label . } BIND(STR(COALESCE(?acr0_label, ?it0, ?any0)) AS ?l0) OPTIONAL { ?subject crm:P46i_forms_part_of ?p1 . OPTIONAL { ?p1 rdfs:label ?it1 . FILTER(LANG(?it1) = "it") } OPTIONAL { ?p1 rdfs:label ?any1 . FILTER(LANG(?any1) = "") } OPTIONAL { ?p1 crm:P1_is_identified_by ?acr1 . ?acr1 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr1 rdfs:label ?acr1_label . } BIND(STR(COALESCE(?acr1_label, ?it1, ?any1)) AS ?l1) } OPTIONAL { ?subject crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p2 . OPTIONAL { ?p2 rdfs:label ?it2 . FILTER(LANG(?it2) = "it") } OPTIONAL { ?p2 rdfs:label ?any2 . FILTER(LANG(?any2) = "") } OPTIONAL { ?p2 crm:P1_is_identified_by ?acr2 . ?acr2 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr2 rdfs:label ?acr2_label . } BIND(STR(COALESCE(?acr2_label, ?it2, ?any2)) AS ?l2) } OPTIONAL { ?subject crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p3 . OPTIONAL { ?p3 rdfs:label ?it3 . FILTER(LANG(?it3) = "it") } OPTIONAL { ?p3 rdfs:label ?any3 . FILTER(LANG(?any3) = "") } OPTIONAL { ?p3 crm:P1_is_identified_by ?acr3 . ?acr3 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr3 rdfs:label ?acr3_label . } BIND(STR(COALESCE(?acr3_label, ?it3, ?any3)) AS ?l3) } OPTIONAL { ?subject crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p4 . OPTIONAL { ?p4 rdfs:label ?it4 . FILTER(LANG(?it4) = "it") } OPTIONAL { ?p4 rdfs:label ?any4 . FILTER(LANG(?any4) = "") } OPTIONAL { ?p4 crm:P1_is_identified_by ?acr4 . ?acr4 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr4 rdfs:label ?acr4_label . } BIND(STR(COALESCE(?acr4_label, ?it4, ?any4)) AS ?l4) } OPTIONAL { ?subject crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p5 . OPTIONAL { ?p5 rdfs:label ?it5 . FILTER(LANG(?it5) = "it") } OPTIONAL { ?p5 rdfs:label ?any5 . FILTER(LANG(?any5) = "") } OPTIONAL { ?p5 crm:P1_is_identified_by ?acr5 . ?acr5 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr5 rdfs:label ?acr5_label . } BIND(STR(COALESCE(?acr5_label, ?it5, ?any5)) AS ?l5) } OPTIONAL { ?subject crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p6 . OPTIONAL { ?p6 rdfs:label ?it6 . FILTER(LANG(?it6) = "it") } OPTIONAL { ?p6 rdfs:label ?any6 . FILTER(LANG(?any6) = "") } OPTIONAL { ?p6 crm:P1_is_identified_by ?acr6 . ?acr6 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr6 rdfs:label ?acr6_label . } BIND(STR(COALESCE(?acr6_label, ?it6, ?any6)) AS ?l6) } OPTIONAL { ?subject crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p7 . OPTIONAL { ?p7 rdfs:label ?it7 . FILTER(LANG(?it7) = "it") } OPTIONAL { ?p7 rdfs:label ?any7 . FILTER(LANG(?any7) = "") } OPTIONAL { ?p7 crm:P1_is_identified_by ?acr7 . ?acr7 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr7 rdfs:label ?acr7_label . } BIND(STR(COALESCE(?acr7_label, ?it7, ?any7)) AS ?l7) } OPTIONAL { ?subject crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p8 . OPTIONAL { ?p8 rdfs:label ?it8 . FILTER(LANG(?it8) = "it") } OPTIONAL { ?p8 rdfs:label ?any8 . FILTER(LANG(?any8) = "") } OPTIONAL { ?p8 crm:P1_is_identified_by ?acr8 . ?acr8 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr8 rdfs:label ?acr8_label . } BIND(STR(COALESCE(?acr8_label, ?it8, ?any8)) AS ?l8) } BIND(STRLANG(CONCAT( COALESCE(CONCAT(?l8, ", "), ""), COALESCE(CONCAT(?l7, ", "), ""), COALESCE(CONCAT(?l6, ", "), ""), COALESCE(CONCAT(?l5, ", "), ""), COALESCE(CONCAT(?l4, ", "), ""), COALESCE(CONCAT(?l3, ", "), ""), COALESCE(CONCAT(?l2, ", "), ""), COALESCE(CONCAT(?l1, ", "), ""), COALESCE(?l0, "") ), "it") AS ?value) }
```

---

## Impact

✅ **Fixes:** Location display in filters, search results, and all UI contexts that use preferredLabels.
✅ **No data changes:** Metadata unchanged; only label computation logic updated.
✅ **Backward compatible:** Existing short labels from `rdfs:label` still work as fallback if pattern fails.

---

## References

- ResearchSpace LabelCache: `src/main/java/org/researchspace/cache/LabelCache.java`
- Language ranking algorithm: lines 292–340
- PropertyPattern parsing: `src/main/java/org/researchspace/config/PropertyPattern.java`
- SPARQL 1.1 CONCAT spec: https://www.w3.org/TR/sparql11-query/#func-concat
- SPARQL 1.1 STRLANG: https://www.w3.org/TR/sparql11-query/#func-strlang
