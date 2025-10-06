# VeNiss SPARQL Queries Documentation

This directory contains SPARQL queries for data management and enrichment in the VeNiss (Venice Digital Archive) system. The queries work with CIDOC-CRM ontology and related extensions to manage different entity types and their associated metadata.

## Overview

The VeNiss query collection is organized by entity type, with each entity having its own directory containing specialized queries for that entity's data management needs:

- **Primary Sources**: Queries for managing archival primary source documents
- **Secondary Sources**: Queries for managing secondary source documents and publications
- **Person**: Queries for person entities and biographical data
- **Group**: Queries for group/actor entities including formation and dissolution data
- **Event**: Queries for event entities with multilingual support

## Directory Structure

```
data/queries/
├── README.md                    # This file - main documentation
├── primary_sources/             # Primary source entity queries
│   ├── search_term.rq          # Generate composite search terms
│   ├── location/               # Archival location management
│   │   ├── seed.sparql         # Initialize root collection paths
│   │   ├── populate.rq         # Create child collection paths
│   │   ├── populate_specific.rq # Update specific collections
│   │   ├── run_sparql_query.sh # Execution script
│   │   └── .env.template       # Environment configuration
│   ├── provenance/             # Digital provenance management
│   │   ├── 01_create_form_records_for_subjects_with_prov_and_no_record.rq
│   │   ├── 02_import_modification_events_from_prov_all.rq
│   │   ├── 03_import_creation_event_from_earliest_prov_all.rq
│   │   └── 04_verify_after_import.rq
│   └── patterns/               # Common patterns and utilities
├── secondary_sources/           # Secondary source entity queries
│   └── search_term.rq          # Generate composite search terms
├── person/                     # Person entity queries
│   └── search_term.rq          # Generate person search terms
├── group/                      # Group/Actor entity queries
│   └── search_term.rq          # Generate group search terms
├── event/                      # Event entity queries
│   └── search_term.rq          # Generate event search terms
├── merge_tables.sql            # SQL utility for table operations
└── postgres_getall.pgsql       # PostgreSQL data retrieval query
```

## Entity-Based Organization

### 📄 Primary Sources ([`primary_sources/`](primary_sources/))

**Entity Type**: `veniss_ontology:Source_Primary`

**Purpose**: Manage archival primary source documents including manuscripts, maps, drawings, and other historical materials.

**Key Capabilities**:
- **Search Term Generation**: Create composite search terms combining titles, locations, islands, and dates
- **Location Management**: Hierarchical archival path construction for collections
- **Provenance Tracking**: Import and manage digital provenance from PROV-O data
- **Pattern Libraries**: Reusable query components for primary source operations

**Main Queries**:
- [`search_term.rq`](primary_sources/search_term.rq) - Generate searchable appellations
- [`location/seed.sparql`](primary_sources/location/seed.sparql) - Initialize collection paths
- [`location/populate.rq`](primary_sources/location/populate.rq) - Build hierarchical paths

### 👤 Person ([`person/`](person/))

**Entity Type**: `veniss_ontology:Person`

**Purpose**: Manage individual people and their biographical information in the historical record.

**Key Capabilities**:
- **Search Term Generation**: Create composite search terms combining names, aliases, patronymics, and dates
- **Name Authority Control**: Handle complex naming patterns including given names, family names, and aliases
- **Biographical Data**: Manage birth/death dates and patronymic information
- **Identity Management**: Support for multiple name forms and appellations

**Main Queries**:
- [`search_term.rq`](person/search_term.rq) - Generate searchable appellations for persons
