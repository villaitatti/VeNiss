#!/usr/bin/env python3
"""
Reconcile Cesium 3D-tile building meshes (metapolis-xdtiler manifests) against
the RDF store's Buildings, using the same join the map uses:

    3D manifest.buildings[code] --(isl_code + "_BLDG_" + code)--> bw_id
    bw_id --(rdfs:label on a P138i_has_representation node)--> building_iri

For each island manifest reachable via /proxy/xdtiler3d, reports:
  - ORPHAN meshes: a 3D code with no matching bw_id anywhere in the RDF store
    (the mesh would be unclickable / dead-linked on the map).
  - AMBIGUOUS meshes: a 3D code whose bw_id resolves to more than one building
    (a duplicate-label data problem; the map would pick one arbitrarily).
  - Buildings with no mesh: informational coverage gap, not an error.

Read-only. Exits non-zero if any orphan or ambiguous code is found in any island.

Usage:
  python3 utils/reconcile_3dtiles.py                  # try all known island codes
  python3 utils/reconcile_3dtiles.py --island LZV      # just one island
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import sparql_query as sq

XDTILER3D_BASE = "https://veniss.net/proxy/xdtiler3d/tiles/ifc"

# Candidate island codes, drawn from the ones referenced in data/templates/Map.html
# and config/services/geosql.ttl per-island table names. Manifests that 404 are
# skipped silently -- not every island has a 3D tileset yet.
CANDIDATE_ISLANDS = [
    "LZV", "PVG", "SSP", "SSC", "CRT", "SSV", "MDM", "LZN",
    "BUR", "CER", "LEG", "POV", "SFD", "SGA", "SGM", "SGP",
    "SLA", "SMI", "STA", "STO",
]


def fetch_manifest(island: str) -> dict | None:
    url = f"{XDTILER3D_BASE}/{island}/manifest.json"
    req = urllib.request.Request(url, headers={"User-Agent": sq.USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    except urllib.error.URLError:
        return None


def rdf_building_counts(endpoint: str, username: str, password: str, island: str) -> dict:
    """Map base bw_id code (e.g. '13' from 'LZV_BLDG_13' or 'LZV_BLDG_13.2') to
    the number of distinct buildings that code resolves to via the map's join."""
    query = f"""
    PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?label (COUNT(DISTINCT ?b) AS ?n) WHERE {{
        ?phase crm:P138i_has_representation ?rep .
        ?rep rdfs:label ?label .
        ?pc crm:P166i_had_presence ?phase .
        ?b crm:P196i_is_defined_by ?pc .
        FILTER(STRSTARTS(STR(?label), "{island}_BLDG_"))
    }} GROUP BY ?label
    """
    result = sq.run_query(endpoint, query, username, password, False)
    counts = {}
    for row in result.get("results", {}).get("bindings", []):
        label = row["label"]["value"]
        n = int(row["n"]["value"])
        base = re.sub(r"\.\d+$", "", label).replace(f"{island}_BLDG_", "")
        counts[base] = max(counts.get(base, 0), n)
    return counts


def reconcile_island(endpoint: str, username: str, password: str, island: str, manifest: dict) -> bool:
    """Returns True if this island is clean (no orphans, no ambiguity)."""
    codes_3d = set(manifest.get("buildings", {}).keys())
    rdf_counts = rdf_building_counts(endpoint, username, password, island)
    codes_rdf = set(rdf_counts.keys())

    orphans = sorted(codes_3d - codes_rdf, key=lambda c: (len(c), c))
    ambiguous = sorted((c for c in codes_3d & codes_rdf if rdf_counts[c] > 1),
                       key=lambda c: (len(c), c))
    uncovered = sorted(codes_rdf - codes_3d, key=lambda c: (len(c), c))

    print(f"\n=== {island}: {len(codes_3d)} meshes, {len(codes_rdf)} RDF building codes ===")
    if orphans:
        print(f"  ORPHAN meshes (no RDF building, dead click): {orphans}")
    if ambiguous:
        print(f"  AMBIGUOUS meshes (resolve to >1 building): {ambiguous}")
    if uncovered:
        print(f"  Buildings with no mesh (coverage gap, informational): {uncovered}")
    if not orphans and not ambiguous:
        print("  OK: every mesh resolves to exactly one building.")

    return not orphans and not ambiguous


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--island", help="Restrict to a single island code (e.g. LZV)")
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    env = sq.load_env(repo_root / ".env")
    endpoint = env.get("SPARQL_ENDPOINT", "https://veniss.net/sparql")
    username = env.get("SPARQL_USERNAME", "")
    password = env.get("SPARQL_PASSWORD", "")

    islands = [args.island] if args.island else CANDIDATE_ISLANDS

    clean = True
    checked = 0
    for island in islands:
        manifest = fetch_manifest(island)
        if manifest is None:
            continue
        checked += 1
        if not reconcile_island(endpoint, username, password, island, manifest):
            clean = False

    if checked == 0:
        print("No 3D tilesets found for the given island(s).")

    sys.exit(0 if clean else 1)


if __name__ == "__main__":
    main()
