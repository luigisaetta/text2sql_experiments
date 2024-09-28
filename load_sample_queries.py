"""
Load sample queries

Load a set of sample queries in the VECTOR database
"""

import json
import oracledb

from utils import get_console_logger
from config import CONNECT_ARGS_VECTOR, TABLE_NAME_SQ

SAMPLES_FILE = "sample_queries.json"

logger = get_console_logger()

# to clear the table before loading
DELETE_QUERY = f"DELETE FROM {TABLE_NAME_SQ}"

INSERT_QUERY = f"""
    INSERT INTO {TABLE_NAME_SQ} (table_name, sample_query)
    VALUES (:table_name, :sample_query)
"""

logger.info("")
logger.info("Loading samples queries in Vector DB...")
logger.info("")

# Read the JSON file
with open(SAMPLES_FILE, "r", encoding="UTF-8") as file:
    data = json.load(file)

try:
    with oracledb.connect(**CONNECT_ARGS_VECTOR) as conn:
        # Create a cursor
        cursor = conn.cursor()

        # Delete all records from the table before inserting new ones
        cursor.execute(DELETE_QUERY)
        conn.commit()

        logger.info("Deleted old data...")

        # Loop over the JSON data
        for entry in data:
            table_name = entry["table"]  # Get the table name
            sample_queries = entry["sample_queries"]  # Get the list of sample queries

            # Insert each sample query into the database
            for query in sample_queries:
                cursor.execute(
                    INSERT_QUERY, {"table_name": table_name, "sample_query": query}
                )

        conn.commit()
        cursor.close()

        logger.info("%s samples queries inserted successfully!", len(data))
        logger.info("")


except oracledb.DatabaseError as e:
    # Rollback the transaction if there is any error
    conn.rollback()
    logger.error("Error inserting data: %s", e)
