"""
To test a newer and faster method for metadata and samples generation
"""

import oracledb

from core_functions import format_schema
from utils import get_console_logger
from config import CONNECT_ARGS, N_SAMPLES, DEBUG
from config_private import DB_USER


logger = get_console_logger()


def get_raw_schema(connection, schema_owner=DB_USER, n_samples=N_SAMPLES):
    """
    This function reads metadata and sample data for each table
    """
    # the dict that will contain the raw schema
    output_dict = {"table_info": "", "table_names": ""}

    try:
        # Create a cursor object
        cursor = connection.cursor()

        # to simplify DDL generation removing info not needed
        cursor.execute(
            """
            BEGIN
                DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 
                'STORAGE', FALSE);
                DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 
                'TABLESPACE', FALSE);
                DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 
                'SEGMENT_ATTRIBUTES', FALSE);
                DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 
                'CONSTRAINTS_AS_ALTER', TRUE);
            END;
        """
        )

        # Query to get the table names sorted alphabetically
        query = """
            SELECT table_name
            FROM all_tables
            WHERE owner = :schema_owner
            ORDER BY table_name
        """

        # Execute the query
        cursor.execute(query, schema_owner=schema_owner)

        # Fetch all table names
        tables = cursor.fetchall()

        # to memorize all the tables
        table_names = []

        # Iterate through each table and get its CREATE TABLE statement
        for table in tables:
            table_name = table[0]
            table_names.append(table_name)

            # Use DBMS_METADATA to generate the CREATE TABLE statement
            cursor.execute(
                f"""
                SELECT DBMS_METADATA.GET_DDL('TABLE', '{table_name}', '{schema_owner}')
                FROM dual
            """
            )

            # Fetch the DDL
            ddl_lob = cursor.fetchone()[0]

            # Remove the collate clauses
            # Convert LOB to string
            ddl = ddl_lob.read() if isinstance(ddl_lob, oracledb.LOB) else ddl_lob
            ddl_cleaned = ddl.replace('COLLATE "USING_NLS_COMP"', "")
            ddl_cleaned = ddl_cleaned.replace('DEFAULT COLLATION "USING_NLS_COMP"', "")
            # remove schema from ddl
            ddl_cleaned = ddl_cleaned.replace(f'"{schema_owner}".', "")
            # remove "
            ddl_cleaned = ddl_cleaned.replace('"', "")

            # Build output for table info
            table_info = f"{ddl_cleaned}\n\n"

            if DEBUG:
                logger.info(table_info)

            # add output to dict
            output_dict["table_info"] += table_info

            # Query to get the first 3 records from the table
            try:
                cursor.execute(
                    f"SELECT * FROM {schema_owner}.{table_name} FETCH FIRST {n_samples} ROWS ONLY"
                )
                records = cursor.fetchall()

                # Get the column names for better formatting
                columns = [col[0] for col in cursor.description]

                # output for records
                records_info = f"--- First {n_samples} records from {table_name} ---\n"
                if records:
                    # add columns headers
                    records_info += " | ".join(columns) + "\n"

                    # add records
                    for record in records:
                        records_info += str(record) + "\n"
                else:
                    records_info += f"No records found in {table_name}\n"

                if DEBUG:
                    logger.info(records_info)

                # add output to dict
                output_dict["table_info"] += records_info + "\n"

            except Exception as e:
                error_message = f"Error retrieving records from {table_name}: {e}\n"
                logger.error(error_message)
                # add nothings
                output_dict["table_info"] += "\n"

        # add table names comma separated
        output_dict["table_names"] = ", ".join(table_names)

    except Exception as e:
        logger.error("Error: %s", e)

    finally:
        # Close the cursor
        if cursor:
            cursor.close()

    return output_dict


#
# Main
#
# Connect to Oracle database
conn = oracledb.connect(**CONNECT_ARGS)

logger.info("")
logger.info("Reading DB schema...")
logger.info("")

# Stampa il contenuto del dizionario
raw_schema = get_raw_schema(conn, schema_owner=DB_USER)

SCHEMA = format_schema(raw_schema)

print("")
print("------ Schema ------")
print("")
print(SCHEMA)
print()

conn.close()
