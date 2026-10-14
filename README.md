# VeNiss

## ⚠️ How to contribute — read this first

> **Never commit to `master`.** GitHub rejects direct pushes to `master`, for everyone (admins included). Every change goes through a branch → CI → pull request.

1. **Branch off `master`**
   ```bash
   git checkout master && git pull
   git checkout -b my-change
   ```
2. **Bump `plugin.version`** in `plugin.properties` (it becomes the PR title).
3. **Validate locally** before pushing (same checks as CI):
   ```bash
   pip install rdflib
   python .github/scripts/validate.py
   ```
4. **Push the branch**: `git push -u origin my-change`
5. **CI runs automatically** (`.github/workflows/ci.yml`). If the `validate` check passes, CI **opens the pull request to `master` for you**, titled `{branch}: vX.Y.Z`. If it fails, fix the errors shown in the Actions log and push again.
6. **Fill in the PR description**: explain *why* the system is being updated. Every PR documents the reason for the new version.
7. **Merge** once `validate` is green. `master` only accepts merges whose check passed on an up-to-date branch.

### What CI checks

| Check | Fails on |
|-------|----------|
| Secrets | `config/repositories/default.ttl` or `.env` committed |
| RDF | Turtle/TriG syntax errors in `config/` and `data/` (`.ttl`, `.trig`) |
| SPARQL | Syntax errors in `.sparql` files |
| Handlebars | Unbalanced `[[#…]]`/`[[/…]]` and `{{#…}}`/`{{/…}}` blocks in templates and page layouts |
| Templates | Template file names that are not URL-encoded IRIs |
| Python | Syntax errors in `utils/*.py` |
| Properties | Malformed lines in `.prop`/`.properties` files |

Unbalanced HTML tags in templates are reported as **warnings** (they do not fail the build). Review them anyway.

## Security

In development mode, all the passwords needs to be passed as JAVA OPTS. Add the following code to the `build.gradle` file, replacing the passwords:

```
"-Dsecret.geo.username=DB_USERNAME",
"-Dsecret.geo.password=DB_PASSWORD",

"-Dsecret.default.username=ARCHIPELAGO_USERNAME",
"-Dsecret.default.password=ARCHIPELAGO_PASSWORD",

"-Dconfig.proxy.mapbox.tokenQueryValue=API_KEY",
```

while on config files set: `${default.username}`

## Default.ttl

For development, set username and password and then move this file to ./config/repositories/default.ttl. Or follow

```
@prefix rep: <http://www.openrdf.org/config/repository#> .
@prefix sail: <http://www.openrdf.org/config/sail#> .
@prefix sr: <http://www.openrdf.org/config/repository/sail#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix mph: <http://www.researchspace.org/resource/system/repository#> .
@prefix ephedra: <http://www.researchspace.org/resource/system/ephedra#> .
@prefix fedsail: <http://www.openrdf.org/config/sail/federation#> .
@prefix sparqlr: <http://www.openrdf.org/config/repository/sparql#> .
[] a rep:Repository;
  rep:repositoryID "default";
  rdfs:label "Default HTTP SPARQL Repository";
  rep:repositoryImpl [
      rep:repositoryType "researchspace:SPARQLBasicAuthRepository";
      sparqlr:query-endpoint <https://veniss.net/sparql>;
      mph:quadMode true;
      mph:writable true;
      mph:username "${default.username}" ;
      mph:password "${default.password}" ;
    ] .
```

test2