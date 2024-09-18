"""
Test read samples query from DB
"""

import oracledb

from utils import get_console_logger
from config import CONNECT_ARGS_VECTOR

logger = get_console_logger()

# Connessione al database Oracle
connection = oracledb.connect(**CONNECT_ARGS_VECTOR)

# Query per ottenere i dati dalla tabella sample_queries
SELECT_QUERY = "SELECT table_name, sample_query FROM sample_queries"

logger.info("")
logger.info("Loading samples queries from DB...")

try:
    # Creazione del cursore
    cursor = connection.cursor()

    # Esecuzione della query
    cursor.execute(SELECT_QUERY)

    # Creazione della struttura tables_dict
    tables_dict = {}

    # Cicla attraverso i risultati della query
    for table_name, sample_query in cursor:
        # Normalizza il table_name in maiuscolo
        table_name = table_name.upper()

        # Aggiungi il sample_query alla lista nel dizionario
        if table_name in tables_dict:
            tables_dict[table_name]["sample_queries"].append(sample_query)
        else:
            tables_dict[table_name] = {"sample_queries": [sample_query]}

    # Stampa tables_dict per debug
    print(tables_dict)

    TABLE_NAME = "AP_INVOICES"

    print(TABLE_NAME)
    queries_list = tables_dict.get(TABLE_NAME, None)["sample_queries"]
    QUERIES_STRING = "\n".join(queries_list)

    print(QUERIES_STRING)

except oracledb.DatabaseError as e:
    print(f"Errore durante la lettura dei dati: {e}")

finally:
    # Chiusura del cursore e della connessione
    cursor.close()
    connection.close()
