#!/usr/bin/env python3
"""
SPARQL query helper for Blazegraph.

Usage:
  python3 utils/sparql_query.py --query "SELECT ..."        # read-only SELECT/ASK
  python3 utils/sparql_query.py --update --query "INSERT ..." # write (requires --update)
  echo "SELECT ..." | python3 utils/sparql_query.py        # query from stdin

Credentials and endpoint are read from .env in the repo root (SPARQL_USERNAME,
SPARQL_PASSWORD, SPARQL_ENDPOINT). Falls back to http://localhost:10214/blazegraph/sparql.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# veniss.net is behind Cloudflare, which blocks the default Python-urllib
# User-Agent (HTTP 403 error 1010) regardless of valid credentials.
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"


def load_env(env_path: Path) -> dict:
    env = {}
    if not env_path.exists():
        return env
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env


def is_write_query(query: str) -> bool:
    normalized = re.sub(r"#[^\n]*", "", query)
    normalized = re.sub(r'""".*?"""', "", normalized, flags=re.DOTALL)
    normalized = re.sub(r"'''.*?'''", "", normalized, flags=re.DOTALL)
    normalized = re.sub(r'"[^"]*"', "", normalized)
    normalized = re.sub(r"'[^']*'", "", normalized)
    return bool(re.search(r"\b(INSERT|DELETE|LOAD|CLEAR|DROP|CREATE|ADD|MOVE|COPY)\b",
                          normalized, re.IGNORECASE))


def run_query(endpoint: str, query: str, username: str, password: str, update: bool) -> dict:
    if update:
        url = endpoint
        data = urllib.parse.urlencode({"update": query}).encode()
        req = urllib.request.Request(url, data=data,
                                     headers={"Content-Type": "application/x-www-form-urlencoded",
                                              "Accept": "application/json",
                                              "User-Agent": USER_AGENT})
    else:
        params = urllib.parse.urlencode({"query": query})
        url = f"{endpoint}?{params}"
        req = urllib.request.Request(url, headers={"Accept": "application/sparql-results+json",
                                                    "User-Agent": USER_AGENT})

    import base64
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    req.add_header("Authorization", f"Basic {credentials}")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode()
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                return {"raw": body}
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def format_results(result: dict) -> None:
    if "raw" in result:
        print(result["raw"])
        return
    if "boolean" in result:
        print(f"ASK result: {result['boolean']}")
        return
    if "results" in result and "bindings" in result["results"]:
        bindings = result["results"]["bindings"]
        if not bindings:
            print("(no results)")
            return
        vars_ = result.get("head", {}).get("vars", [])
        col_widths = {v: max(len(v), max((len(b.get(v, {}).get("value", "")) for b in bindings), default=0))
                      for v in vars_}
        header = "  ".join(v.ljust(col_widths[v]) for v in vars_)
        print(header)
        print("-" * len(header))
        for b in bindings:
            row = "  ".join(b.get(v, {}).get("value", "").ljust(col_widths[v]) for v in vars_)
            print(row)
        print(f"\n({len(bindings)} row{'s' if len(bindings) != 1 else ''})")
        return
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Run SPARQL queries against Blazegraph.")
    parser.add_argument("--query", "-q", help="SPARQL query string (reads stdin if omitted)")
    parser.add_argument("--update", action="store_true",
                        help="Required for INSERT/DELETE/UPDATE queries")
    parser.add_argument("--json", action="store_true", help="Print raw JSON response")
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    env = load_env(repo_root / ".env")

    endpoint = env.get("SPARQL_ENDPOINT", "http://localhost:10214/blazegraph/sparql")
    username = env.get("SPARQL_USERNAME", "")
    password = env.get("SPARQL_PASSWORD", "")

    if args.query:
        query = args.query
    else:
        query = sys.stdin.read().strip()

    if not query:
        print("Error: no query provided.", file=sys.stderr)
        sys.exit(1)

    if is_write_query(query) and not args.update:
        print("Error: this query contains write operations (INSERT/DELETE/etc.).", file=sys.stderr)
        print("Re-run with --update to confirm you intend to modify production data.", file=sys.stderr)
        sys.exit(2)

    result = run_query(endpoint, query, username, password, args.update)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        format_results(result)


if __name__ == "__main__":
    main()
