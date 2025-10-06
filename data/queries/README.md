# VeNiss SPARQL Queries Documentation

This directory contains SPARQL queries for data management and enrichment in the VeNiss (Venice Digital Archive) system. The queries work with CIDOC-CRM ontology and related extensions to manage different entity types and their associated metadata.

## Overview

The VeNiss query collection is organized by entity type, with each entity having its own directory containing specialized queries for that entity's data management needs:

- **Primary Sources**: Queries for managing archival primary source documents
- **Collections**: Queries for archival collection hierarchies (planned)
- **Actors**: Queries for person and organization entities (planned)
- **Built Works**: Queries for architectural and urban structures (planned)

## Directory Structure

```
data/queries/
├── README.md                    # This file - main documentation
├── primary_sources/             # Primary source entity queries
│   ├── README.md               # Primary sources documentation
│   ├── search_term.sparql      # Generate composite search terms
│   ├── location/               # Archival location management
│   │   ├── seed.sparql         # Initialize root collection paths
│   │   ├── populate.sparql     # Create child collection paths
│   │   ├── populate_specific.sparql # Update specific collections
│   │   ├── run_sparql_query.sh # Execution script
│   │   └── .env.template       # Environment configuration
│   ├── provenance/             # Digital provenance management
│   │   ├── 01_create_form_records_for_subjects_with_prov_and_no_record.rq
│   │   ├── 02_import_modification_events_from_prov_all.rq
│   │   ├── 03_import_creation_event_from_earliest_prov_all.rq
│   │   └── 04_verify_after_import.rq
│   └── patterns/               # Common patterns and utilities
├── merge_tables.sql            # SQL utility for table operations
├── postgres_getall.pgsql       # PostgreSQL data retrieval query
├── labels/                     # Label management queries (legacy)
├── location/                   # Location queries (legacy - moved to primary_sources)
├── provenance/                 # Provenance queries (legacy - moved to primary_sources)
└── search_terms/               # Search term queries (legacy - moved to primary_sources)
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
- [`search_term.sparql`](primary_sources/search_term.sparql) - Generate searchable appellations
- [`location/seed.sparql`](primary_sources/location/seed.sparql) - Initialize collection paths
- [`location/populate.sparql`](primary_sources/location/populate.sparql) - Build hierarchical paths
- [`provenance/01_create_form_records_for_subjects_with_prov_and_no_record.rq`](primary_sources/provenance/01_create_form_records_for_subjects_with_prov_and_no_record.rq) - Create form records

### 🏛️ Collections (Planned)

**Entity Type**: `crm:E78_Collection`

**Purpose**: Manage archival collection hierarchies and organizational structures.

**Planned Capabilities**:
- Collection hierarchy management
- Metadata inheritance patterns
- Access control and permissions
- Collection-level statistics

### 👥 Actors (Planned)

**Entity Type**: `veniss_ontology:Actor`, `veniss_ontology:Person`

**Purpose**: Manage people, organizations, and other agents in the historical record.

**Planned Capabilities**:
- Name authority control
- Biographical data management
- Role and relationship tracking
- Temporal activity periods

### 🏗️ Built Works (Planned)

**Entity Type**: `veniss_ontology:Builtwork`

**Purpose**: Manage architectural structures, urban features, and built environment data.

**Planned Capabilities**:
- Spatial relationship management
- Temporal state tracking
- Architectural typology classification
- Geographic integration

## Ontologies and Standards

### Core Ontologies
- **CIDOC-CRM**: Conceptual Reference Model for cultural heritage information
- **CRMdig**: CIDOC-CRM Digital extension for digital provenance
- **PROV-O**: W3C Provenance Ontology
- **RDF/RDFS**: Resource Description Framework and Schema

### VeNiss-Specific Extensions
- **VeNiss Ontology**: Domain-specific classes and properties for Venetian historical data
- **VeNiss Types**: Controlled vocabulary for type classifications

## Common Patterns

### Namespace Prefixes
```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX crmdig: <http://www.ics.forth.gr/isl/CRMdig/>
PREFIX veniss_ontology: <https://veniss.net/ontology#>
PREFIX veniss_types: <https://veniss.net/resource/type/>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
```

### Entity Type Patterns
```sparql
# Primary Sources
?item rdf:type veniss_ontology:Source_Primary .

# Collections
?collection rdf:type crm:E78_Collection .

# Actors
?actor rdf:type veniss_ontology:Actor .
```

### Idempotency Pattern
All queries implement idempotency to prevent duplicate data:
```sparql
FILTER NOT EXISTS {
  # Check for existing data before insertion
}
```

### IRI Generation
Consistent IRI patterns for new resources:
```sparql
# Predictable IRIs
BIND(IRI(CONCAT(STR(?subject), "/suffix")) AS ?newResource)

# Unique IRIs with UUIDs
BIND(IRI(CONCAT(STR(?subject), "/", STRUUID())) AS ?uniqueResource)
```

## Execution Guidelines

### Entity-Specific Workflows

#### Primary Sources Complete Setup
```bash
# 1. Location hierarchy (if new collections)
cd primary_sources/location
./run_sparql_query.sh seed.sparql
./run_sparql_query.sh populate.sparql

# 2. Provenance import (if PROV data exists)
cd ../provenance
sparql-query 01_create_form_records_for_subjects_with_prov_and_no_record.rq
sparql-query 02_import_modification_events_from_prov_all.rq
sparql-query 03_import_creation_event_from_earliest_prov_all.rq

# 3. Search term generation
cd ..
sparql-query search_term.sparql

# 4. Verification
cd provenance
sparql-query 04_verify_after_import.rq
```

### Prerequisites by Entity Type

#### Primary Sources
- Entities must be typed as `veniss_ontology:Source_Primary`
- Attributed titles should be present with language tags
- Archival collection hierarchies should be established
- PROV data should be available in container graphs (for provenance)

### Performance Considerations
- **Entity-Specific Indexing**: Index on entity type properties for each category
- **Batch Processing**: Most queries designed for batch execution within entity types
- **Memory Management**: Large entity collections may require query optimization
- **Incremental Updates**: Use entity-specific patterns for targeted updates

## Migration from Legacy Structure

### Legacy Directories
The following directories contain the original functional organization and will be maintained for backward compatibility:

- [`location/`](location/) - Original location queries (now in `primary_sources/location/`)
- [`provenance/`](provenance/) - Original provenance queries (now in `primary_sources/provenance/`)
- [`search_terms/`](search_terms/) - Original search queries (now in `primary_sources/search_term.sparql`)

### Migration Path
1. **Current State**: Both structures exist for compatibility
2. **Transition Period**: Update scripts and documentation to use new structure
3. **Future State**: Legacy directories will be removed once migration is complete

## Integration with VeNiss System

### Data Flow by Entity Type
1. **Base Data Import**: Entity-specific data loading
2. **Entity Enrichment**: Type-specific metadata enhancement
3. **Cross-Entity Relationships**: Linking between entity types
4. **Discovery Enhancement**: Search and navigation improvements

### System Components
- **Triplestore**: RDF data storage with entity-specific graphs
- **Web Interface**: Entity-specific browse and search interfaces
- **Import Pipeline**: Entity-aware data processing workflows
- **API Endpoints**: RESTful access to entity-specific data

## Development Guidelines

### Adding New Entity Types
1. Create new directory: `data/queries/{entity_type}/`
2. Include standard subdirectories: `patterns/`, entity-specific functional areas
3. Create entity-specific README.md with documentation
4. Update this main README with new entity information
5. Follow established naming conventions and patterns

### Query Development Standards
- **Entity Scoping**: All queries should be scoped to specific entity types
- **Idempotency**: Implement existence checks to prevent duplicates
- **Documentation**: Include comprehensive inline comments
- **Testing**: Provide verification queries where appropriate
- **Performance**: Consider batch processing and indexing requirements

## Troubleshooting

### Entity-Specific Issues
- **Type Validation**: Ensure entities have correct `rdf:type` declarations
- **Cross-Entity Dependencies**: Verify related entities exist before creating relationships
- **Namespace Consistency**: Use consistent namespace prefixes across entity types

### General Debugging
- Use entity-specific `SELECT` queries to preview results
- Check entity type distributions with count queries
- Validate cross-entity relationships
- Monitor query performance by entity type

## Related Documentation

- [Primary Sources Queries Documentation](primary_sources/README.md)
- [SPARQL Cron Setup](../../SPARQL_CRON_SETUP.md)
- [Legacy Location Queries](location/README.md) (deprecated)
- [Legacy Provenance Queries](provenance/README.md) (deprecated)
- [Legacy Search Terms Queries](search_terms/README.md) (deprecated)

---

*This documentation covers the entity-based SPARQL query organization for the VeNiss digital archive system. For system-wide documentation, see the main project README.*