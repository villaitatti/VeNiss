# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VeNiss (plugin id: `VeNiss`, provider: VIT, version: 0.0.1) is a [ResearchSpace](https://researchspace.org/) plugin for managing Venetian islands and buildings as cultural heritage data. It models entities (Islands, Buildings, Events, Persons, Groups, Sources) using the CIDOC-CRM ontology and exposes them through a semantic web interface at veniss.net.

This repo contains **only the plugin assets** — no standalone server. It runs inside a ResearchSpace deployment.

## Development Setup

There is no `package.json` or standalone build script. Deployment is via ResearchSpace's plugin loading mechanism.

**Required secrets** (passed as JAVA_OPTS in the host ResearchSpace `build.gradle`):

```
-Dsecret.geo.username=DB_USERNAME
-Dsecret.geo.password=DB_PASSWORD
-Dsecret.default.username=SPARQL_USERNAME
-Dsecret.default.password=SPARQL_PASSWORD
-Dconfig.proxy.mapbox.tokenQueryValue=MAPBOX_API_KEY
```

Within config files, reference these as `${default.username}`, `${default.password}`, etc.

**`config/repositories/default.ttl`** is excluded from version control. Create it manually for development using the template in `README.md`, pointing to the SPARQL endpoint at `https://veniss.net/sparql`.

## Architecture

### Data Stores

- **RDF triple store**: SPARQL endpoint at `https://veniss.net/sparql` — stores all semantic/heritage data
- **PostgreSQL/PostGIS**: `jdbc:postgresql://10.10.1.10:5432/veniss_prod` — stores geospatial island/building geometries
- **Ephedra federation** (`config/repositories/ephedra.ttl`): federated repository combining the geo SQL service, the default SPARQL store, and OSM Nominatim

### UI Layer

Page layout is defined in Handlebars templates (`config/page-layout/`). Page content uses ResearchSpace web components embedded in HTML:

- `<semantic-search>` / `<semantic-query>` — SPARQL-backed search and display
- `<semantic-map>` — Mapbox-powered interactive map
- `<mp-event-proxy>` / `<mp-event-target-template-render>` — reactive state propagation between components

SPARQL queries are written inline in template attributes or loaded from `.sparql` files in `assets/`.

### Data Model

Entities follow CIDOC-CRM. Key namespace prefixes are in `config/namespaces.prop` (`veniss:`, `crm:`, `crmpc:`, etc.).

Islands and buildings support **temporal phases** with `bob`/`eoe` fields (begin of begin / end of end), sourced from PostgreSQL and exposed via the Ephedra geosql service.

SQL-to-SPARQL bindings for all geospatial queries are defined as named services in `config/services/geosql.ttl`. Templates query these via `SERVICE <.../federation#geosql> { ... }`.

## Key Directories

| Path | Purpose |
|------|---------|
| `config/` | ResearchSpace config: repositories, services, namespaces, UI properties, page-layout |
| `data/templates/` | HTML page templates using RS web components |
| `data/field-definitions/` | TRIG files defining RDF form field bindings |
| `data/queries/` | SPARQL queries; `location/populate.sparql` runs hourly via cron |
| `assets/` | CSS, icons, images, standalone `.sparql` files |
| `utils/` | Python scripts for generating TTL/SPARQL from CSV/TSV source data |

## Cron Job

`run_sparql_query.sh` (root of repo) executes `data/queries/location/populate.sparql` hourly. This query builds hierarchical location paths for archival collections. Credentials are read from `.env` (excluded from version control — see `SPARQL_CRON_SETUP.md`).

## Contribution Rules

- `master` is read-only. All changes require a pull request.
- PR branch names must follow the format `{branch}: vX.Y.Z`.
