"""
Test read sample queries

only to check that changes are working with new format for json file
"""

import json

SAMPLES_FILE = "sample_queries.json"

with open(SAMPLES_FILE, "r", encoding="UTF-8") as file:
    data = json.load(file)

    # create a dictionary where key is table_name
    # and value is a dict with one field: sample queries
    tables_dict = {}
    for element in data:
        table_name = element.get("table")
        if table_name:
            # normalize in uppercase
            table_name = table_name.upper()
            tables_dict[table_name] = {"sample_queries": element.get("sample_queries")}

print("")
print(tables_dict)
print("")

table_name = "AP_INVOICES"

queries_list = tables_dict.get(table_name, None)["sample_queries"]
queries_string = "\n".join(queries_list)

print(queries_string)
