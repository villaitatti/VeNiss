import csv
import re

def transform_names(csv_file_path):
    transformed_names = []

    with open(csv_file_path, 'r') as csvfile:
        csv_reader = csv.reader(csvfile)
        for row in csv_reader:
            for name in row:
                # Convert name to lowercase and remove spaces and special characters
                transformed_name = re.sub(r'[^a-z]', '', name.lower())
                transformed_names.append(transformed_name)

    return transformed_names

csv_file_path = 'islands_list.csv'
result_list = transform_names(csv_file_path)
print(result_list)


element_values = result_list

template = '''
rs_sql_sail:includesSQLQuery
[
    rs_sql_sail:hasQueryId "{element_value}_island_shapes" ;
    rs_sql_sail:text "select distinct \\"BW_ID\\" as bw_id, ST_AsText(geometry) as wkt from qgis_{element_value}_islands"
] ;
'''

# Open file in append mode
with open('islands_shapes_queries.ttl', 'a') as f:
    for element_value in element_values:
        # Format the template string with the current element value
        formatted_template = template.format(element_value=element_value)
        
        # Write the formatted string to the file
        f.write(formatted_template)