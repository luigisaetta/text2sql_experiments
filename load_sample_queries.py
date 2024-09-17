"""
Load sample queries

Load a set of sample queries in the VECTOR database
"""

import json
import oracledb

from utils import get_console_logger
from config import CONNECT_ARGS_VECTOR

SAMPLES_FILE = "sample_queries.json"

logger = get_console_logger()

# Connection to Oracle Database
# Replace these with your actual Oracle connection details
connection = oracledb.connect(**CONNECT_ARGS_VECTOR)

# to clear the table before loading
DELETE_QUERY = "DELETE FROM sample_queries"

INSERT_QUERY = """
    INSERT INTO sample_queries (table_name, sample_query)
    VALUES (:table_name, :sample_query)
"""

# Read the JSON file
with open(SAMPLES_FILE, "r", encoding="UTF-8") as file:
    data = json.load(file)

try:
    # Create a cursor
    cursor = connection.cursor()

    # Delete all records from the table before inserting new ones
    cursor.execute(DELETE_QUERY)
    connection.commit()

    # Loop over the JSON data
    for entry in data:
        table_name = entry["table"]  # Get the table name
        sample_queries = entry["sample_queries"]  # Get the list of sample queries

        # Insert each sample query into the database
        for query in sample_queries:
            cursor.execute(
                INSERT_QUERY, {"table_name": table_name, "sample_query": query}
            )

    connection.commit()

    logger.info("Data inserted successfully!")

except oracledb.DatabaseError as e:
    # Rollback the transaction if there is any error
    connection.rollback()
    logger.error("Error inserting data: %s", e)

finally:
    # Close the cursor and connection
    cursor.close()
    connection.close()
