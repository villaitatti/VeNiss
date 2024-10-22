import csv
import os
import uuid


def read_islands_from_csv(filename):
    """Reads island names from the given CSV file."""
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header if there's any
        islands = [row[0] for row in reader]
    return islands


def transform_island_to_label(island_name):
    return ''.join([c for c in island_name if c.isalpha()]).lower()


def get_island_details(island_name, tsv_file):
    """Fetches details of the given island from the TSV file."""
    with open(tsv_file, 'r') as file:
        reader = csv.reader(file, delimiter='\t')
        for row in reader:
            if row[1] == island_name and row[7] == "ISL":
                return {
                    "island_full_name": island_name,
                    "island_label": transform_island_to_label(island_name),
                    "latitude": row[4],
                    "longitude": row[5],
                    "geonames_id": 'https://www.geonames.org/' + row[0] + '/'
                }
    return None


def generate_sparql_queries(island_details_list):
    queries = []
    
    template_queries = ["""
    CONSTRUCT { <https://veniss.net/resource/builtwork/{{UUID}}> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://veniss.net/ontology#Island>. }
WHERE {  }

CONSTRUCT { <https://veniss.net/resource/builtwork/{{UUID}}> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/P53_Place>. }
WHERE {  }

CONSTRUCT {
  <https://veniss.net/resource/builtwork/{{UUID}}> <http://www.cidoc-crm.org/cidoc-crm/P1_is_identified_by> ?appellation.
  ?appellation <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://www.cidoc-crm.org/cidoc-crm/E41_Appellation>.
  ?appellation <http://www.w3.org/2000/01/rdf-schema#label> "{{ISLAND_FULL_NAME}}"^^<http://www.w3.org/2001/XMLSchema#string>.
}
WHERE { BIND(URI(CONCAT(STR(<https://veniss.net/resource/builtwork/{{UUID}}>), "/appellation")) AS ?appellation) }

CONSTRUCT {
  <https://veniss.net/resource/builtwork/{{UUID}}> <http://www.cidoc-crm.org/cidoc-crm/P48_has_preferred_identifier> ?geonames_identifier.
  ?geonames_identifier <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.cidoc-crm.org/cidoc-crm/E42_Identifier>.
  ?geonames_identifier <http://www.w3.org/2000/01/rdf-schema#label> "{{GEONAMES_IDENTIFIER}}"^^<http://www.w3.org/2001/XMLSchema#string>.
}
WHERE { BIND(URI(CONCAT(STR(<https://veniss.net/resource/builtwork/{{UUID}}>), "/geonames_identifier")) AS ?geonames_identifier) }


CONSTRUCT { <https://veniss.net/resource/builtwork/{{UUID}}> <http://www.w3.org/2000/01/rdf-schema#label> "{{ISLAND_LABEL}}"^^<http://www.w3.org/2001/XMLSchema#string>. }
WHERE {  }

CONSTRUCT {
  <https://veniss.net/resource/builtwork/{{UUID}}> <http://www.cidoc-crm.org/cidoc-crm/P87_is_identified_by> ?latitude.
  ?latitude <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://www.cidoc-crm.org/cidoc-crm/E47_Spatial_Coordinates>.
  ?latitude <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://veniss.net/ontology#latitude>.
  ?latitude <http://www.w3.org/2000/01/rdf-schema#label> "{{LATITUDE}}"^^<http://www.w3.org/2001/XMLSchema#string>.
}
WHERE { BIND(URI(CONCAT(STR(<https://veniss.net/resource/builtwork/{{UUID}}>), "/latitude")) AS ?latitude) }

CONSTRUCT {
  <https://veniss.net/resource/builtwork/{{UUID}}> <http://www.cidoc-crm.org/cidoc-crm/P87_is_identified_by> ?longitude.
  ?longitude <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <http://www.cidoc-crm.org/cidoc-crm/E47_Spatial_Coordinates>.
  ?longitude <http://www.cidoc-crm.org/cidoc-crm/P2_has_type> <https://veniss.net/ontology#longitude>.
  ?longitude <http://www.w3.org/2000/01/rdf-schema#label> "{{LONGITUDE}}"^^<http://www.w3.org/2001/XMLSchema#string>.
}
WHERE { BIND(URI(CONCAT(STR(<https://veniss.net/resource/builtwork/{{UUID}}>), "/longitude")) AS ?longitude) }
    """]
    
    for island in island_details_list:
        new_uuid = str(uuid.uuid4())
        for template in template_queries:
            query = template.replace("{{UUID}}", new_uuid)
            query = query.replace("{{ISLAND_FULL_NAME}}", island["island_full_name"])
            query = query.replace("{{ISLAND_LABEL}}", island["island_label"])
            query = query.replace("{{GEONAMES_IDENTIFIER}}", island["geonames_id"])
            query = query.replace("{{LATITUDE}}", island["latitude"])
            query = query.replace("{{LONGITUDE}}", island["longitude"])
            queries.append(query)
    
    return queries


def generate_ttl_file(island_data):
  ttl_template = """
  @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
  @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
  @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
  @prefix cidoc-crm: <http://www.cidoc-crm.org/cidoc-crm/> .
  @prefix veniss-ontology: <https://veniss.net/ontology#> .

  <https://veniss.net/resource/builtwork/{{UUID}}>
      rdf:type veniss-ontology:Island ;
      rdf:type <http://www.cidoc-crm.org/P53_Place> ;
      rdfs:label "{{ISLAND_LABEL}}"^^xsd:string ;
      cidoc-crm:P1_is_identified_by <https://veniss.net/resource/builtwork/{{UUID}}/appellation> ;
      cidoc-crm:P48_has_preferred_identifier <https://veniss.net/resource/builtwork/{{UUID}}/geonames_identifier> ;
      cidoc-crm:P87_is_identified_by <https://veniss.net/resource/builtwork/{{UUID}}/latitude> ;
      cidoc-crm:P87_is_identified_by <https://veniss.net/resource/builtwork/{{UUID}}/longitude> .

  <https://veniss.net/resource/builtwork/{{UUID}}/appellation>
      cidoc-crm:P2_has_type cidoc-crm:E41_Appellation ;
      rdfs:label "{{ISLAND_FULL_NAME}}"^^xsd:string .

  <https://veniss.net/resource/builtwork/{{UUID}}/geonames_identifier>
      rdf:type cidoc-crm:E42_Identifier ;
      rdfs:label "{{GEONAMES_IDENTIFIER}}"^^xsd:string .

  <https://veniss.net/resource/builtwork/{{UUID}}/latitude>
      cidoc-crm:P2_has_type cidoc-crm:E47_Spatial_Coordinates ;
      cidoc-crm:P2_has_type veniss-ontology:latitude ;
      rdfs:label "{{LATITUDE}}"^^xsd:string .

  <https://veniss.net/resource/builtwork/{{UUID}}/longitude>
      cidoc-crm:P2_has_type cidoc-crm:E47_Spatial_Coordinates ;
      cidoc-crm:P2_has_type veniss-ontology:longitude ;
      rdfs:label "{{LONGITUDE}}"^^xsd:string .

  """

  # Replace placeholders with actual island data
  new_uuid = str(uuid.uuid4())
  ttl_content = ttl_template.replace("{{UUID}}", new_uuid)
  ttl_content = ttl_content.replace("{{ISLAND_LABEL}}", island_data["island_label"])
  ttl_content = ttl_content.replace("{{ISLAND_FULL_NAME}}", island_data["island_full_name"])
  ttl_content = ttl_content.replace("{{GEONAMES_IDENTIFIER}}", island_data["geonames_id"])
  ttl_content = ttl_content.replace("{{LATITUDE}}", island_data["latitude"])
  ttl_content = ttl_content.replace("{{LONGITUDE}}", island_data["longitude"])
  
  # Define the filename for the TTL file
  ttl_filename = f"./islands_ttls/{island_data['island_label']}.ttl"
  
  # Write the TTL content to a new file
  with open(ttl_filename, 'w') as file:
      file.write(ttl_content)
  
  print(f"TTL file generated: {ttl_filename}")


def main():
    islands = read_islands_from_csv('islands_list.csv')
    blacklisted_islands = read_islands_from_csv('islands_blacklist.csv')
    for blacklisted in blacklisted_islands:
        print(f"Blacklisted:{blacklisted}")
    for island in islands:
        print(f"Island:{transform_island_to_label(island)}")
    island_details_list = []

    for island in islands:
        if transform_island_to_label(island) not in blacklisted_islands:
            print(f"Island {island} not in blacklisted")
            details = get_island_details(island, 'it.tsv')
            print(details)
            print("############################################")
            if details:
                island_details_list.append(details)
    
    for island_data in island_details_list:
        generate_ttl_file(island_data)

main()