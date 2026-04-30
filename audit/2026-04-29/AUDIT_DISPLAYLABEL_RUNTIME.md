# displayLabel Staleness — Audit & Resolution
Session: 2026-04-29 (updated 2026-04-30)

---

## Problem

Archival locations in `vocab/archives` use a pre-computed `rs:displayLabel` property to show a hierarchical path string. This pre-computed cache is **stale** (never recomputed when locations are created or parents change) and is **misused** (displayed in contexts where the short label should appear).

### Two Distinct Display Contexts

The same location must be displayed differently depending on context:

| Context | Required display | Example for `vol. V` |
|---------|------------------|----------------------|
| **Authority sidebar / tree navigation** | Short label only | `vol. V` |
| **Filters, source list, parent picker** | Full hierarchical path | `ASTo, Biblioteca antica, Manoscritti, Architettura militare, disegni di piazze e fortificazioni, vol. V` |

### Concrete Example

Location: `<https://veniss.net/resource/archival_entity/a030d4f2-9323-4ebd-9d6a-16a14259ce67>`

Current triples:
```
rdfs:label                "vol. V"@it
rdfs:label                "vol. V"
rs:displayLabel           "ASTo, Biblioteca antica, Manoscritti, Architettura militare, disegni di piazze e fortificazioni, vol. V"
crm:P46i_forms_part_of    <.../b554d33f-...>   # → "Architettura militare, disegni..."
crm:P71i_is_listed_in     <vocab/archives>
```

**What goes wrong today:**
- Authority sidebar shows the full path string instead of just `vol. V` (uses `displayLabel` where it should use `rdfs:label`).
- Filters and lists rely on `displayLabel` — fine when it exists and is current, broken when missing or stale.

---

## Why Not Auto-Compute on Save

ResearchSpace **has no native declarative post-save SPARQL hook**. The form fires `Form.ResourceCreated` / `Form.ResourceUpdated` events, but no built-in component can receive them and execute a SPARQL UPDATE. Implementing one requires writing a custom TypeScript component — out of scope for a config-only project.

**Sources:** `/researchspace/src/main/web/components/forms/ResourceEditorFormConfig.ts`, `FormEvents.ts`, `ResourceEditorForm.ts`.

---

## Resolution

**Delete `rs:displayLabel` everywhere. Compute the full path at runtime in every context that needs it. Let the authority sidebar use `rdfs:label` naturally.**

This is more expensive at query time but **always correct** — no staleness possible.

### Why This Works

| Display context | Source of truth after change |
|-----------------|------------------------------|
| Authority sidebar / tree | `rdfs:label` (already there, no change needed once `displayLabel` is removed) |
| List view `column4` | Runtime SPARQL pattern walking `crm:P46i_forms_part_of` |
| Filter facet (`entity_search_location` KP) | Runtime SPARQL pattern in `selectPattern` / `valueSetPattern` |
| Parent picker (tree-picker in form) | `query-item-label` — already runtime, may need update |
| Source list (resource configurations) | Runtime SPARQL pattern |

---

## Changes Required

### Change 1 — Delete all `rs:displayLabel` triples (cleanup)

**Type:** WRITE — production Blazegraph
**Risk:** Low once runtime patterns are in place. **Must run AFTER changes 2–4 are tested.**

```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX rs: <http://www.researchspace.org/ontology/>

DELETE { ?loc rs:displayLabel ?v }
WHERE {
  ?loc crm:P71i_is_listed_in <http://www.researchspace.org/resource/vocab/archives> .
  ?loc rs:displayLabel ?v .
}
```

**Expected result:** ~427 triples deleted.

---

### Change 2 — Filter KP `entity_search_location`: runtime path in `valueSetPattern`

**Goal:** When the filter facet renders the list of available locations (not a selected value, but the dropdown options), each location's label must be the full runtime-reconstructed path: `Root, Parent, Self`.

**Important distinction:**
- `selectPattern` = "what value is currently selected for THIS subject" (used in forms, one result per subject)
- `valueSetPattern` = "what are ALL possible values available" (used in filters, one result per possible location)

For a filter facet showing available locations, we use `valueSetPattern`.

**Step 2a — Inspect current KP (READ):**
```sparql
SELECT ?prop ?val WHERE {
  <https://veniss.net/container/fieldDefinitionContainer/entity_search_location> ?prop ?val .
}
```

**Step 2b — Replacement pattern for `valueSetPattern` (runtime, 8-level depth, root-first ordered, acronym-aware):**

Walk the `P46i_forms_part_of` hierarchy explicitly at each depth level (up to 8 levels deep, handles the deepest archives), extract acronyms where available, and concatenate in root-first order:

```sparql
SELECT ?value (CONCAT(
  COALESCE(CONCAT(?l8, ", "), ""),
  COALESCE(CONCAT(?l7, ", "), ""),
  COALESCE(CONCAT(?l6, ", "), ""),
  COALESCE(CONCAT(?l5, ", "), ""),
  COALESCE(CONCAT(?l4, ", "), ""),
  COALESCE(CONCAT(?l3, ", "), ""),
  COALESCE(CONCAT(?l2, ", "), ""),
  COALESCE(CONCAT(?l1, ", "), ""),
  COALESCE(?l0, "")
) AS ?label) WHERE {
  ?value crm:P71i_is_listed_in <http://www.researchspace.org/resource/vocab/archives> .
  
  # Level 0 — self
  OPTIONAL { ?value rdfs:label ?it0 . FILTER(LANG(?it0) = "it") }
  OPTIONAL { ?value rdfs:label ?any0 . FILTER(LANG(?any0) = "") }
  OPTIONAL {
    ?value crm:P1_is_identified_by ?acr0 .
    ?acr0 crm:P2_has_type <https://veniss.net/resource/type/acronym> .
    ?acr0 rdfs:label ?acr0_label .
  }
  BIND(COALESCE(?acr0_label, ?it0, ?any0) AS ?l0)
  
  # Level 1 — parent
  OPTIONAL {
    ?value crm:P46i_forms_part_of ?p1 .
    OPTIONAL { ?p1 rdfs:label ?it1 . FILTER(LANG(?it1) = "it") }
    OPTIONAL { ?p1 rdfs:label ?any1 . FILTER(LANG(?any1) = "") }
    OPTIONAL {
      ?p1 crm:P1_is_identified_by ?acr1 .
      ?acr1 crm:P2_has_type <https://veniss.net/resource/type/acronym> .
      ?acr1 rdfs:label ?acr1_label .
    }
    BIND(COALESCE(?acr1_label, ?it1, ?any1) AS ?l1)
  }
  
  # Level 2 — grandparent
  OPTIONAL {
    ?value crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p2 .
    OPTIONAL { ?p2 rdfs:label ?it2 . FILTER(LANG(?it2) = "it") }
    OPTIONAL { ?p2 rdfs:label ?any2 . FILTER(LANG(?any2) = "") }
    OPTIONAL {
      ?p2 crm:P1_is_identified_by ?acr2 .
      ?acr2 crm:P2_has_type <https://veniss.net/resource/type/acronym> .
      ?acr2 rdfs:label ?acr2_label .
    }
    BIND(COALESCE(?acr2_label, ?it2, ?any2) AS ?l2)
  }
  
  # Level 3
  OPTIONAL {
    ?value crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p3 .
    OPTIONAL { ?p3 rdfs:label ?it3 . FILTER(LANG(?it3) = "it") }
    OPTIONAL { ?p3 rdfs:label ?any3 . FILTER(LANG(?any3) = "") }
    OPTIONAL {
      ?p3 crm:P1_is_identified_by ?acr3 .
      ?acr3 crm:P2_has_type <https://veniss.net/resource/type/acronym> .
      ?acr3 rdfs:label ?acr3_label .
    }
    BIND(COALESCE(?acr3_label, ?it3, ?any3) AS ?l3)
  }
  
  # Level 4
  OPTIONAL {
    ?value crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p4 .
    OPTIONAL { ?p4 rdfs:label ?it4 . FILTER(LANG(?it4) = "it") }
    OPTIONAL { ?p4 rdfs:label ?any4 . FILTER(LANG(?any4) = "") }
    OPTIONAL {
      ?p4 crm:P1_is_identified_by ?acr4 .
      ?acr4 crm:P2_has_type <https://veniss.net/resource/type/acronym> .
      ?acr4 rdfs:label ?acr4_label .
    }
    BIND(COALESCE(?acr4_label, ?it4, ?any4) AS ?l4)
  }
  
  # Level 5
  OPTIONAL {
    ?value crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p5 .
    OPTIONAL { ?p5 rdfs:label ?it5 . FILTER(LANG(?it5) = "it") }
    OPTIONAL { ?p5 rdfs:label ?any5 . FILTER(LANG(?any5) = "") }
    OPTIONAL {
      ?p5 crm:P1_is_identified_by ?acr5 .
      ?acr5 crm:P2_has_type <https://veniss.net/resource/type/acronym> .
      ?acr5 rdfs:label ?acr5_label .
    }
    BIND(COALESCE(?acr5_label, ?it5, ?any5) AS ?l5)
  }
  
  # Level 6
  OPTIONAL {
    ?value crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p6 .
    OPTIONAL { ?p6 rdfs:label ?it6 . FILTER(LANG(?it6) = "it") }
    OPTIONAL { ?p6 rdfs:label ?any6 . FILTER(LANG(?any6) = "") }
    OPTIONAL {
      ?p6 crm:P1_is_identified_by ?acr6 .
      ?acr6 crm:P2_has_type <https://veniss.net/resource/type/acronym> .
      ?acr6 rdfs:label ?acr6_label .
    }
    BIND(COALESCE(?acr6_label, ?it6, ?any6) AS ?l6)
  }
  
  # Level 7
  OPTIONAL {
    ?value crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p7 .
    OPTIONAL { ?p7 rdfs:label ?it7 . FILTER(LANG(?it7) = "it") }
    OPTIONAL { ?p7 rdfs:label ?any7 . FILTER(LANG(?any7) = "") }
    OPTIONAL {
      ?p7 crm:P1_is_identified_by ?acr7 .
      ?acr7 crm:P2_has_type <https://veniss.net/resource/type/acronym> .
      ?acr7 rdfs:label ?acr7_label .
    }
    BIND(COALESCE(?acr7_label, ?it7, ?any7) AS ?l7)
  }
  
  # Level 8 — deepest ancestor
  OPTIONAL {
    ?value crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p8 .
    OPTIONAL { ?p8 rdfs:label ?it8 . FILTER(LANG(?it8) = "it") }
    OPTIONAL { ?p8 rdfs:label ?any8 . FILTER(LANG(?any8) = "") }
    OPTIONAL {
      ?p8 crm:P1_is_identified_by ?acr8 .
      ?acr8 crm:P2_has_type <https://veniss.net/resource/type/acronym> .
      ?acr8 rdfs:label ?acr8_label .
    }
    BIND(COALESCE(?acr8_label, ?it8, ?any8) AS ?l8)
  }
}
```

**Why this works:**
- **8 depth levels** — handles deep hierarchies up to 8 levels (e.g., ASVe → Senato → Deliberazioni → Militar → Filze → filza 69 = 6 levels; and deeper archives like Procuratori di San Marco → ... → Fascicolo 2 = 8 levels)
- **Property paths** for explicit depth (`crm:P46i_forms_part_of/crm:P46i_forms_part_of/...`) — Blazegraph-compatible
- **Acronym extraction** — pulls acronyms (e.g., "ASVe") from `P1_is_identified_by` with type=acronym, falls back to labels
- **CONCAT order** (`?l8, ?l7, ?l6, ?l5, ?l4, ?l3, ?l2, ?l1, ?l0`) — hardcoded root-first, guaranteed ordering
- **Language preference** — tries Italian first, then blank language
- **Example output:** `"ASVe, Senato, Deliberazioni, Militar, Filze, filza 69"` ✓

**Step 2c — Dry-run test (completed 2026-04-30):**

Tested the 8-level pattern against live Blazegraph. Results:
- 20 sample locations queried, all returned non-empty hierarchical labels
- Depth range: 1–7 levels (single roots up to deepest archives)
- Example output: "Direzione generale antichità e belle arti (Roma), Divisione seconda , Scavi; musei, gallerie, oggetti d'arte, esportazioni; monumenti / 1908-1924, Pos. 6 Monumenti - Venezia. Burano. Chiesa parrocchiale di Santa Caterina di Mazzorbo (1920)"
- COALESCE chain working: acronyms (e.g., "RAF") preferred over Italian/blank labels
- Concatenation format correct: root-first with ", " separator
- **Status: ✅ Ready to deploy**

**Step 2d — Apply update (WRITE — confirm before firing):**

Minified 8-level pattern for insertion:
```sparql
SELECT ?value (CONCAT(COALESCE(CONCAT(?l8, ", "), ""), COALESCE(CONCAT(?l7, ", "), ""), COALESCE(CONCAT(?l6, ", "), ""), COALESCE(CONCAT(?l5, ", "), ""), COALESCE(CONCAT(?l4, ", "), ""), COALESCE(CONCAT(?l3, ", "), ""), COALESCE(CONCAT(?l2, ", "), ""), COALESCE(CONCAT(?l1, ", "), ""), COALESCE(?l0, "")) AS ?label) WHERE { ?value crm:P71i_is_listed_in <http://www.researchspace.org/resource/vocab/archives> . OPTIONAL { ?value rdfs:label ?it0 . FILTER(LANG(?it0) = "it") } OPTIONAL { ?value rdfs:label ?any0 . FILTER(LANG(?any0) = "") } OPTIONAL { ?value crm:P1_is_identified_by ?acr0 . ?acr0 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr0 rdfs:label ?acr0_label . } BIND(COALESCE(?acr0_label, ?it0, ?any0) AS ?l0) OPTIONAL { ?value crm:P46i_forms_part_of ?p1 . OPTIONAL { ?p1 rdfs:label ?it1 . FILTER(LANG(?it1) = "it") } OPTIONAL { ?p1 rdfs:label ?any1 . FILTER(LANG(?any1) = "") } OPTIONAL { ?p1 crm:P1_is_identified_by ?acr1 . ?acr1 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr1 rdfs:label ?acr1_label . } BIND(COALESCE(?acr1_label, ?it1, ?any1) AS ?l1) } OPTIONAL { ?value crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p2 . OPTIONAL { ?p2 rdfs:label ?it2 . FILTER(LANG(?it2) = "it") } OPTIONAL { ?p2 rdfs:label ?any2 . FILTER(LANG(?any2) = "") } OPTIONAL { ?p2 crm:P1_is_identified_by ?acr2 . ?acr2 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr2 rdfs:label ?acr2_label . } BIND(COALESCE(?acr2_label, ?it2, ?any2) AS ?l2) } OPTIONAL { ?value crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p3 . OPTIONAL { ?p3 rdfs:label ?it3 . FILTER(LANG(?it3) = "it") } OPTIONAL { ?p3 rdfs:label ?any3 . FILTER(LANG(?any3) = "") } OPTIONAL { ?p3 crm:P1_is_identified_by ?acr3 . ?acr3 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr3 rdfs:label ?acr3_label . } BIND(COALESCE(?acr3_label, ?it3, ?any3) AS ?l3) } OPTIONAL { ?value crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p4 . OPTIONAL { ?p4 rdfs:label ?it4 . FILTER(LANG(?it4) = "it") } OPTIONAL { ?p4 rdfs:label ?any4 . FILTER(LANG(?any4) = "") } OPTIONAL { ?p4 crm:P1_is_identified_by ?acr4 . ?acr4 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr4 rdfs:label ?acr4_label . } BIND(COALESCE(?acr4_label, ?it4, ?any4) AS ?l4) } OPTIONAL { ?value crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p5 . OPTIONAL { ?p5 rdfs:label ?it5 . FILTER(LANG(?it5) = "it") } OPTIONAL { ?p5 rdfs:label ?any5 . FILTER(LANG(?any5) = "") } OPTIONAL { ?p5 crm:P1_is_identified_by ?acr5 . ?acr5 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr5 rdfs:label ?acr5_label . } BIND(COALESCE(?acr5_label, ?it5, ?any5) AS ?l5) } OPTIONAL { ?value crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p6 . OPTIONAL { ?p6 rdfs:label ?it6 . FILTER(LANG(?it6) = "it") } OPTIONAL { ?p6 rdfs:label ?any6 . FILTER(LANG(?any6) = "") } OPTIONAL { ?p6 crm:P1_is_identified_by ?acr6 . ?acr6 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr6 rdfs:label ?acr6_label . } BIND(COALESCE(?acr6_label, ?it6, ?any6) AS ?l6) } OPTIONAL { ?value crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p7 . OPTIONAL { ?p7 rdfs:label ?it7 . FILTER(LANG(?it7) = "it") } OPTIONAL { ?p7 rdfs:label ?any7 . FILTER(LANG(?any7) = "") } OPTIONAL { ?p7 crm:P1_is_identified_by ?acr7 . ?acr7 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr7 rdfs:label ?acr7_label . } BIND(COALESCE(?acr7_label, ?it7, ?any7) AS ?l7) } OPTIONAL { ?value crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p8 . OPTIONAL { ?p8 rdfs:label ?it8 . FILTER(LANG(?it8) = "it") } OPTIONAL { ?p8 rdfs:label ?any8 . FILTER(LANG(?any8) = "") } OPTIONAL { ?p8 crm:P1_is_identified_by ?acr8 . ?acr8 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr8 rdfs:label ?acr8_label . } BIND(COALESCE(?acr8_label, ?it8, ?any8) AS ?l8) } }
```

Full UPDATE query:
```sparql
PREFIX field: <http://www.researchspace.org/resource/system/fields/>

DELETE {
  <https://veniss.net/container/fieldDefinitionContainer/entity_search_location>
    field:valueSetPattern ?old .
}
INSERT {
  <https://veniss.net/container/fieldDefinitionContainer/entity_search_location>
    field:valueSetPattern """SELECT ?value (CONCAT(COALESCE(CONCAT(?l8, ", "), ""), COALESCE(CONCAT(?l7, ", "), ""), COALESCE(CONCAT(?l6, ", "), ""), COALESCE(CONCAT(?l5, ", "), ""), COALESCE(CONCAT(?l4, ", "), ""), COALESCE(CONCAT(?l3, ", "), ""), COALESCE(CONCAT(?l2, ", "), ""), COALESCE(CONCAT(?l1, ", "), ""), COALESCE(?l0, "")) AS ?label) WHERE { ?value crm:P71i_is_listed_in <http://www.researchspace.org/resource/vocab/archives> . OPTIONAL { ?value rdfs:label ?it0 . FILTER(LANG(?it0) = "it") } OPTIONAL { ?value rdfs:label ?any0 . FILTER(LANG(?any0) = "") } OPTIONAL { ?value crm:P1_is_identified_by ?acr0 . ?acr0 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr0 rdfs:label ?acr0_label . } BIND(COALESCE(?acr0_label, ?it0, ?any0) AS ?l0) OPTIONAL { ?value crm:P46i_forms_part_of ?p1 . OPTIONAL { ?p1 rdfs:label ?it1 . FILTER(LANG(?it1) = "it") } OPTIONAL { ?p1 rdfs:label ?any1 . FILTER(LANG(?any1) = "") } OPTIONAL { ?p1 crm:P1_is_identified_by ?acr1 . ?acr1 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr1 rdfs:label ?acr1_label . } BIND(COALESCE(?acr1_label, ?it1, ?any1) AS ?l1) } OPTIONAL { ?value crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p2 . OPTIONAL { ?p2 rdfs:label ?it2 . FILTER(LANG(?it2) = "it") } OPTIONAL { ?p2 rdfs:label ?any2 . FILTER(LANG(?any2) = "") } OPTIONAL { ?p2 crm:P1_is_identified_by ?acr2 . ?acr2 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr2 rdfs:label ?acr2_label . } BIND(COALESCE(?acr2_label, ?it2, ?any2) AS ?l2) } OPTIONAL { ?value crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p3 . OPTIONAL { ?p3 rdfs:label ?it3 . FILTER(LANG(?it3) = "it") } OPTIONAL { ?p3 rdfs:label ?any3 . FILTER(LANG(?any3) = "") } OPTIONAL { ?p3 crm:P1_is_identified_by ?acr3 . ?acr3 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr3 rdfs:label ?acr3_label . } BIND(COALESCE(?acr3_label, ?it3, ?any3) AS ?l3) } OPTIONAL { ?value crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p4 . OPTIONAL { ?p4 rdfs:label ?it4 . FILTER(LANG(?it4) = "it") } OPTIONAL { ?p4 rdfs:label ?any4 . FILTER(LANG(?any4) = "") } OPTIONAL { ?p4 crm:P1_is_identified_by ?acr4 . ?acr4 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr4 rdfs:label ?acr4_label . } BIND(COALESCE(?acr4_label, ?it4, ?any4) AS ?l4) } OPTIONAL { ?value crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p5 . OPTIONAL { ?p5 rdfs:label ?it5 . FILTER(LANG(?it5) = "it") } OPTIONAL { ?p5 rdfs:label ?any5 . FILTER(LANG(?any5) = "") } OPTIONAL { ?p5 crm:P1_is_identified_by ?acr5 . ?acr5 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr5 rdfs:label ?acr5_label . } BIND(COALESCE(?acr5_label, ?it5, ?any5) AS ?l5) } OPTIONAL { ?value crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p6 . OPTIONAL { ?p6 rdfs:label ?it6 . FILTER(LANG(?it6) = "it") } OPTIONAL { ?p6 rdfs:label ?any6 . FILTER(LANG(?any6) = "") } OPTIONAL { ?p6 crm:P1_is_identified_by ?acr6 . ?acr6 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr6 rdfs:label ?acr6_label . } BIND(COALESCE(?acr6_label, ?it6, ?any6) AS ?l6) } OPTIONAL { ?value crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p7 . OPTIONAL { ?p7 rdfs:label ?it7 . FILTER(LANG(?it7) = "it") } OPTIONAL { ?p7 rdfs:label ?any7 . FILTER(LANG(?any7) = "") } OPTIONAL { ?p7 crm:P1_is_identified_by ?acr7 . ?acr7 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr7 rdfs:label ?acr7_label . } BIND(COALESCE(?acr7_label, ?it7, ?any7) AS ?l7) } OPTIONAL { ?value crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of/crm:P46i_forms_part_of ?p8 . OPTIONAL { ?p8 rdfs:label ?it8 . FILTER(LANG(?it8) = "it") } OPTIONAL { ?p8 rdfs:label ?any8 . FILTER(LANG(?any8) = "") } OPTIONAL { ?p8 crm:P1_is_identified_by ?acr8 . ?acr8 crm:P2_has_type <https://veniss.net/resource/type/acronym> . ?acr8 rdfs:label ?acr8_label . } BIND(COALESCE(?acr8_label, ?it8, ?any8) AS ?l8) } }""" .
}
WHERE {
  <https://veniss.net/container/fieldDefinitionContainer/entity_search_location>
    field:valueSetPattern ?old .
}
```

---

### Change 3 — List view `column4`: update resource config SPARQL pattern

**Goal:** When the list view of a search renders the location column for a row, walk the hierarchy at runtime instead of reading `displayLabel`.

**Step 3a — Find current pattern (READ):**
```sparql
PREFIX rs_col: <http://www.researchspace.org/pattern/system/resource_search_listView_column/>
PREFIX rs_cfg: <http://www.researchspace.org/pattern/system/resource_configuration/>

SELECT ?config ?col4 ?pattern WHERE {
  ?config rs_cfg:resource_search_listView_column ?col4 .
  ?col4 rs_col:order "4" ;
        rs_col:content_sparql_pattern ?pattern .
}
```

**Step 3b — Replacement pattern:** same shape as Change 2 (the runtime hierarchy walk), adapted to the variable bindings expected by `column4` (`?item`, `?value`, `?label`).

**Step 3c — Apply update (WRITE — confirm before firing).**

---

### Change 4 — Parent picker in `Archival_unit.html` form

The form's tree-picker uses `query-item-label`:

```sparql
SELECT ?label where {
  ?item crm:P1_is_identified_by ?path_app .
  ?path_app a crm:E41_Appellation ;
    crm:P2_has_type veniss_types:path ;
    rdfs:label ?label .
}
```

This already reads from a separate `path` appellation, **not** from `displayLabel` — so it is not directly affected by Change 1. However, if those `path` appellations are ALSO stale (created at the same time as `displayLabel`), they have the same problem.

**Verify:** Run a small audit on the `path` appellations to confirm whether they are pre-computed too. If yes, replace this `query-item-label` with the runtime hierarchy pattern.

```sparql
# Audit query — does the path appellation reflect current hierarchy?
SELECT ?loc ?pathLabel ?currentLabel ?parentLabel WHERE {
  ?loc crm:P71i_is_listed_in <http://www.researchspace.org/resource/vocab/archives> .
  ?loc crm:P1_is_identified_by ?path_app .
  ?path_app crm:P2_has_type <https://veniss.net/resource/vocab/types/path> .
  ?path_app rdfs:label ?pathLabel .
  ?loc rdfs:label ?currentLabel .
  OPTIONAL { ?loc crm:P46i_forms_part_of ?parent . ?parent rdfs:label ?parentLabel }
}
LIMIT 20
```

---

### Change 5 — Source list / parent column displays

Any other resource configuration listing locations (Source_Primary, Source_Secondary, etc.) that uses a `resource_search_listView_column` reading `displayLabel` needs the same runtime pattern as Change 3. Discover them with:

```sparql
PREFIX rs_col: <http://www.researchspace.org/pattern/system/resource_search_listView_column/>

SELECT ?col ?pattern WHERE {
  ?col rs_col:content_sparql_pattern ?pattern .
  FILTER(CONTAINS(STR(?pattern), "displayLabel"))
}
```

This finds every column config that depends on the cached label. Each one needs to be rewritten to use the runtime hierarchy walk before Change 1 (the delete) runs.

---

## Execution Order (Strict)

| # | Step | Type | Purpose |
|---|------|------|---------|
| 1 | Inspect filter KP `entity_search_location` | READ | Know current valueSetPattern |
| 2 | Inspect resource config `column4` patterns | READ | Know current pattern |
| 3 | Discover all column patterns referencing `displayLabel` (Change 5 query) | READ | Full inventory |
| 4 | Audit `path` appellations (Change 4 query) | READ | Decide if path picker needs update |
| 5 | Update filter KP `valueSetPattern` (ordered, runtime path) | WRITE | Filter facet shows runtime root→leaf path |
| 6 | Update each affected column `content_sparql_pattern` | WRITE | List view shows runtime path |
| 7 | (If needed) Update parent picker `query-item-label` in `Archival_unit.html` | EDIT (file) | Tree-picker shows runtime path |
| 8 | UI test: filter facet, list view, sidebar, parent picker | UI | Verify all four contexts |
| 9 | Delete all `rs:displayLabel` triples (Change 1) | WRITE | Final cleanup |
| 10 | UI re-test | UI | Confirm sidebar now shows short label |

**Do not run step 9 until steps 5–8 are validated** — otherwise filters/lists will fall back to `rdfs:label` only and lose the path display.

---

## Verification

After all changes:

1. **Sidebar / authority tree** — `vol. V` displays as `vol. V`, not the full path.
2. **Filter facet** — selecting `vol. V` shows `ASTo, Biblioteca antica, Manoscritti, Architettura militare, disegni di piazze e fortificazioni, vol. V`.
3. **List view (column4)** — same full path renders for sources linked to `vol. V`.
4. **Parent picker** in Archival_unit form — full path appears in the tree-picker.
5. **New location creation** — create a leaf under any parent; immediately filter on it; full path appears with no manual displayLabel needed.
6. **Parent change** — move a location to a new parent via SPARQL UPDATE; reload the filter; new path appears immediately.
7. **Performance** — open a search with 20+ results; column4 renders within ~1s.

---

## Out of Scope (Separate Issues)

While inspecting `<.../a030d4f2-9323-4ebd-9d6a-16a14259ce67>` (vol. V), two unrelated data quality issues surfaced:

1. **Duplicate `P2_has_type`**: the location has both
   - `<vocab/archival_unit_types/360fd62e-...>` (correct: "Archival item / Unità documentaria")
   - `<vocab/information_carrier/location>` (wrong vocab — value labelled "location")

   The "location" entry shown in the Typology dropdown in the form UI comes from the `information_carrier` vocab, not from `archival_unit_types`. The typology KP should constrain its `valueSetPattern` to `archival_unit_types` only, and existing wrong-vocab values should be removed.

2. **Two `P1_is_identified_by` appellations** (`/path` and `/search_term/...`): structure not yet documented; needs its own audit before any cleanup.

These are tracked separately and should not be bundled into this change.

---

## Files & Resources

| Resource | Path / IRI |
|----------|------------|
| List template | `data/templates/http%3A%2F%2Fwww.researchspace.org%2Fresource%2FResourceSearchTemplate.html` |
| Archival unit form | `data/templates/http%3A%2F%2Fveniss.net%2Fforms%2Fvocab%2FArchival_unit.html` |
| Filter KP | `https://veniss.net/container/fieldDefinitionContainer/entity_search_location` |
| Authority | `http://www.researchspace.org/resource/vocab/archives` (E32_Authority_Document) |
| Properties (live) | `crm:P46i_forms_part_of`, `rdfs:label` |
| Property to remove | `rs:displayLabel` |

---

## Implementation Checklist (Execution Order)

### Phase 1: Add Per-Context Runtime Overrides (Steps 1–4)

**[STEP 1] Add `valueSetPattern` to filter KP `entity_search_location`**
- **What:** INSERT the 8-level hierarchy walk as `field:valueSetPattern` into Blazegraph
- **Where:** Blazegraph KP `https://veniss.net/container/fieldDefinitionContainer/entity_search_location`
- **Pattern:** Minified 8-level from audit Step 2d (lines 248–249)
- **Query:** Full UPDATE from audit Step 2d (lines 252–267)
- **Verification:** Open search UI → expand Location filter → confirm each option shows full path (e.g., "ASVe, Senato, Deliberazioni, …, filza 69")

**[STEP 2] Override `column4` resource config `content_sparql_pattern`**
- **What:** Find and REPLACE the current pattern in archival resource config's `column4` with the 8-level walk
- **Where:** Blazegraph resource config, column with `order "4"`
- **First query:** Run Step 3a (audit lines 277–285) to find the current pattern
- **Then update:** Replace with same 8-level walk as Step 1, adapted to variables expected by column (`?item`, `?value`, `?label`)
- **Verification:** Run search returning 10+ archival-entity results → column 4 shows full hierarchical paths

**[STEP 3] Inventory all other `content_sparql_pattern` references to `displayLabel`**
- **What:** Find every resource config column/pattern that uses the stale `rs:displayLabel`
- **Query:** Run the inventory query from audit Step 5 (lines 330–335)
- **Then patch each:** Replace each hit's pattern with the 8-level walk (same as Steps 1–2)
- **Files to check:** Search over `data/templates/` for `displayLabel` references; likely matches in Source_Primary and Source_Secondary configs
- **Verification:** For each column patched, verify it displays the full path in search results

**[STEP 4] Audit and (if needed) update parent picker `query-item-label` in form**
- **What:** Check if the `path` appellation (used by the tree-picker in Archival_unit form) is also stale
- **Query:** Run the audit query from audit Step 4 (lines 313–321) — compare `pathLabel` vs current `crm:P46i_forms_part_of` hierarchy
- **Decision:**
  - If `pathLabel` matches current hierarchy: no change needed
  - If `pathLabel` is stale: replace `query-item-label` in `Archival_unit.html` (lines 75–82) with the 8-level pattern
- **Verification:** Open Archival_unit form → expand parent picker → select a location with children → confirm tree shows both parent and children with short labels (not full paths)

### Phase 2: UI Verification (Step 5)

**[STEP 5] Test all four display contexts**
1. **Filter facet:** Search → expand Location filter → confirm each option shows full path
2. **List view (column4):** Return 10+ results → column 4 shows full paths for each row
3. **Sidebar/authority tree:** Navigate to a location in the sidebar → should show only short label (e.g., "vol. V", not the full path)
4. **Parent picker in form:** Archival_unit form → expand parent selector → tree shows short labels for each node
5. **Performance:** Open search with 20+ results → column 4 renders within ~1 sec

### Phase 3: Data Cleanup (Step 6)

**[STEP 6] Delete all `rs:displayLabel` triples**
- **When:** Only after Steps 1–5 are verified and working
- **Query:** Run deletion from audit Step 1 (lines 71–79)
- **Expected result:** ~427 triples deleted
- **Post-deletion verification:**
  - Sidebar now shows short labels only ✓
  - Filter, column4, form all still show full paths (via new patterns) ✓
  - No errors in logs ✓

---

## Current Status

| Step | Task | Status |
|------|------|--------|
| 2c | Dry-run 8-level pattern on Blazegraph | ✅ Complete |
| 1 | Wire `valueSetPattern` to filter KP | ⏳ Ready (pattern validated) |
| 2 | Override column4 resource config | ⏳ Ready (pattern validated) |
| 3 | Inventory & patch all `displayLabel` patterns | ⏳ Ready |
| 4 | Audit & fix parent picker (if needed) | ⏳ Ready |
| 5 | UI verification (all four contexts) | ⏳ Pending Step 1 |
| 6 | Delete `rs:displayLabel` triples | ⏳ Last (after Step 5 verified) |
