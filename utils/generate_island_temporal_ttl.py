#!/usr/bin/env python3
"""
Script to generate TTL entries for temporal island data queries.
This creates entries that use the get_island_temporal_data SQL function.
"""

import csv

# Mapping for islands with different table names than their display names
ISLAND_TABLE_MAPPINGS = {
    'lacertosa': 'certosa',
    'lagrazia': 'legrazie',
    # Add any other mappings as needed
}

def normalize_island_name(island):
    """Convert island name to match table naming convention."""
    # Check if there's a special mapping
    if island in ISLAND_TABLE_MAPPINGS:
        return ISLAND_TABLE_MAPPINGS[island]
    
    # Some specific transformations based on the existing patterns in geosql.ttl
    replacements = {
        'santerasmo': 'santerasmo',  # Keep as is
        'santospirito': 'santospirito',
        'santacristina': 'santacristina',
        'santandrea': 'santandrea',
        'santangelodellapolvere': 'santangelodellapolvere',
        'santariano': 'santariano',
    }
    
    return replacements.get(island, island)

def generate_ttl_entry(island):
    """Generate a TTL entry for an island's temporal query."""
    table_name = normalize_island_name(island)
    query_id = f"{table_name}_island_shapes_temporal"
    
    # SQL query that transforms geometries from EPSG:4326 to EPSG:3857 (Web Mercator)
    sql_query = f"""SELECT DISTINCT 
        data.identifier::text as bw_id,
        ST_AsText(ST_Transform(data.geometry, 3857))::text as wkt,
        COALESCE(sy.start::text, 
            CASE 
                WHEN col_data.key = 'today' THEN '2023'
                ELSE SUBSTRING(col_data.key FROM '^(\\\\d{{4}})')
            END
        )::text as bob,
        COALESCE(sy.end::text,
            CASE 
                WHEN col_data.key = 'today' THEN '2025'
                ELSE SUBSTRING(col_data.key FROM '^(\\\\d{{4}})')
            END
        )::text as eoe
    FROM public.qgis_{table_name}_islands data,
    LATERAL jsonb_each_text(
        to_jsonb(data) - 'identifier' - 'geometry' - 'identifier_short' - 'name'
    ) as col_data
    LEFT JOIN production.sources_years sy ON sy.source = col_data.key
    WHERE col_data.value::boolean = true"""
    
    # Escape the query for TTL - replace newlines and quotes
    sql_query = sql_query.replace('\n', ' ').replace('"', '\\"')
    
    # Generate the TTL entry
    ttl_entry = f"""rs_sql_sail:includesSQLQuery
[
    rs_sql_sail:hasQueryId "{query_id}" ;
    rs_sql_sail:text "{sql_query}"
] ;
"""
    
    return ttl_entry

def main():
    # Read islands from CSV
    islands = []
    with open('islands_blacklist.csv', 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            if row:  # Skip empty rows
                islands.append(row[0].strip())
    
    # Generate TTL content
    ttl_content = """# Temporal island data queries using the get_island_temporal_data function
# Generated automatically for use in geosql.ttl

"""
    
    for island in islands:
        ttl_content += generate_ttl_entry(island) + "\n"
    
    # Remove the last semicolon and replace with period
    ttl_content = ttl_content.rstrip(";\n") + " .\n"
    
    # Write to output file
    output_file = 'island_temporal_queries.ttl'
    with open(output_file, 'w') as f:
        f.write(ttl_content)
    
    print(f"Generated {len(islands)} TTL entries in {output_file}")
    print(f"You can now copy the content of {output_file} into geosql.ttl")

if __name__ == "__main__":
    main()
