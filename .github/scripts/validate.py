#!/usr/bin/env python3
"""
Static checks that catch changes which would break the VeNiss plugin once it
is loaded by ResearchSpace. Run locally before pushing:

    pip install rdflib
    python .github/scripts/validate.py

Only files tracked by git are checked, so local-only files such as
config/repositories/default.ttl and .env are ignored (but fail if committed).
"""

import html.parser
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

from rdflib import Dataset, Graph
from rdflib.plugins.sparql.parser import parseQuery, parseUpdate

ROOT = Path(__file__).resolve().parents[2]

# Files that hold credentials and must never reach the repository.
FORBIDDEN = ["config/repositories/default.ttl", ".env"]

# utils/ holds generated Turtle snippets meant to be pasted into other files.
RDF_SKIP_DIRS = ("utils",)

# Prefixes RDF4J (used by ResearchSpace) resolves even when a file does not declare them.
# Kept on one line so reported line numbers match the file.
DEFAULT_PREFIXES = (
    "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> . "
    "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> . "
    "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> . "
    "@prefix owl: <http://www.w3.org/2002/07/owl#> . "
)

VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}
# Tags the browser closes implicitly; their balance is not meaningful.
OPTIONAL_CLOSE_TAGS = {"p", "li", "dt", "dd", "option", "tr", "td", "th", "thead", "tbody"}

# Templates mix server-side [[...]] and client-side {{...}} Handlebars;
# block helpers of each flavour are checked separately.
BLOCK_TOKENS = {
    "[[": re.compile(r"\[\[\[\[(/?)(\w+)[^\]]*\]\]\]\]|\[\[(#\*?>?|/)\s*([\w-]+)[^\]]*\]\]"),
    "{{": re.compile(r"\{\{\{\{(/?)(\w+)[^}]*\}\}\}\}|\{\{(#\*?>?|/)\s*([\w-]+)[^}]*\}\}"),
}
COMMENTS = re.compile(r"\[\[!--.*?--\]\]|\[\[!.*?\]\]|\{\{!--.*?--\}\}|\{\{!.*?\}\}", re.S)
EXPRESSIONS = re.compile(r"\[\[.*?\]\]|\{\{.*?\}\}", re.S)
TAG_NAME = re.compile(r"^[a-z][a-z0-9-]*$")

errors = []
warnings = []


def error(path, message):
    errors.append(f"{path}: {message}")


def warning(path, message):
    warnings.append(f"{path}: {message}")


def tracked_files():
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout
    return [Path(p) for p in out.splitlines() if (ROOT / p).is_file()]


def check_forbidden(files):
    names = {f.as_posix() for f in files}
    for path in FORBIDDEN:
        if path in names:
            error(path, "contains credentials and must not be committed (see .gitignore)")


def check_rdf(path):
    text = (ROOT / path).read_text(encoding="utf-8")
    try:
        if path.suffix == ".trig":
            Dataset().parse(data=DEFAULT_PREFIXES + text, format="trig")
        else:
            Graph().parse(data=DEFAULT_PREFIXES + text, format="turtle")
    except Exception as e:
        error(path, f"invalid RDF syntax: {e}")


def check_sparql(path):
    text = (ROOT / path).read_text(encoding="utf-8")
    try:
        parseQuery(text)
        return
    except Exception as e:
        query_error = e
    try:
        parseUpdate(text)
        return
    except Exception:
        pass
    # Also accept graph-pattern snippets (PREFIX lines followed by triple patterns).
    prologue = "\n".join(l for l in text.splitlines() if l.strip().upper().startswith("PREFIX"))
    body = "\n".join(l for l in text.splitlines() if not l.strip().upper().startswith("PREFIX"))
    try:
        parseQuery(f"{prologue}\nSELECT * WHERE {{\n{body}\n}}")
    except Exception:
        error(path, f"invalid SPARQL syntax: {query_error}")


def check_python(path):
    try:
        compile((ROOT / path).read_text(encoding="utf-8"), str(path), "exec")
    except SyntaxError as e:
        error(path, f"line {e.lineno}: Python syntax error: {e.msg}")


def strip_handlebars(text):
    # Remove comments and expressions so they do not confuse the HTML parser,
    # keeping newlines so reported line numbers stay correct.
    blank = lambda m: "\n" * m.group(0).count("\n")
    return EXPRESSIONS.sub(blank, COMMENTS.sub(blank, text))


class TagBalanceParser(html.parser.HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.stack = []

    @staticmethod
    def ignored(tag):
        # Skips void tags and IRIs such as <https://...> inside inline SPARQL.
        return tag in VOID_TAGS or tag in OPTIONAL_CLOSE_TAGS or not TAG_NAME.match(tag)

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_starttag(self, tag, attrs):
        if not self.ignored(tag):
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if self.ignored(tag):
            return
        if any(t == tag for t, _ in self.stack):
            while self.stack:
                open_tag, line = self.stack.pop()
                if open_tag == tag:
                    return
                warning(self.path, f"line {line}: <{open_tag}> is never closed")
        else:
            warning(self.path, f"line {self.getpos()[0]}: </{tag}> has no matching opening tag")

    def finish(self):
        self.close()
        for tag, line in self.stack:
            warning(self.path, f"line {line}: <{tag}> is never closed")


def check_html(path):
    text = (ROOT / path).read_text(encoding="utf-8")
    parser = TagBalanceParser(path)
    parser.feed(strip_handlebars(text))
    parser.finish()


def check_handlebars(path):
    blank = lambda m: "\n" * m.group(0).count("\n")
    text = COMMENTS.sub(blank, (ROOT / path).read_text(encoding="utf-8"))
    for brace, token in BLOCK_TOKENS.items():
        close = "]]" if brace == "[[" else "}}"
        stack = []
        for m in token.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            if m.group(2):  # raw blocks: [[[[raw]]]] ... [[[[/raw]]]]
                closing, name = m.group(1) == "/", m.group(2)
            else:
                closing, name = m.group(3) == "/", m.group(4)
            if not closing:
                stack.append((name, line))
            elif not stack:
                error(path, f"line {line}: {brace}/{name}{close} has no matching opening block")
            else:
                open_name, open_line = stack.pop()
                if open_name != name:
                    error(path, f"line {line}: {brace}/{name}{close} closes {brace}#{open_name}{close} opened at line {open_line}")
        for name, line in stack:
            error(path, f"line {line}: {brace}#{name}{close} is never closed")


def check_template_name(path):
    iri = unquote(path.stem)
    if not re.match(r"^https?://\S+$", iri):
        error(path, f"template file name must be a URL-encoded IRI, got '{iri}'")


def check_properties(path):
    for n, line in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if stripped and not stripped.startswith(("#", "!")) and "=" not in stripped and ":" not in stripped:
            error(path, f"line {n}: expected 'key = value', got '{stripped}'")


def main():
    files = tracked_files()
    check_forbidden(files)
    for path in files:
        if path.suffix in (".ttl", ".trig") and path.parts[0] not in RDF_SKIP_DIRS:
            check_rdf(path)
        elif path.suffix == ".sparql":
            check_sparql(path)
        elif path.suffix == ".py":
            check_python(path)
        elif path.suffix in (".prop", ".properties"):
            check_properties(path)
        if path.suffix in (".html", ".hbs"):
            check_html(path)
            check_handlebars(path)
        if path.suffix == ".html" and path.parts[:2] == ("data", "templates"):
            check_template_name(path)

    # HTML tag balance is only a warning: ResearchSpace's parser tolerates some
    # stray tags, so treat these as hints to review rather than blockers.
    if warnings:
        print(f"{len(warnings)} warning(s) (unbalanced HTML tags, please review):\n")
        print("\n".join(warnings) + "\n")
    if errors:
        print(f"{len(errors)} error(s) found:\n")
        print("\n".join(errors))
        sys.exit(1)
    print(f"All checks passed ({len(files)} tracked files).")


if __name__ == "__main__":
    main()
