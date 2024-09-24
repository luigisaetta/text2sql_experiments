"""
Schema info step by step
"""

from tqdm import tqdm
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from database_manager import DatabaseManager
from llm_manager import LLMManager

from config import (
    MODEL_LIST,
    MODEL_ENDPOINTS,
    TEMPERATURE,
    CONNECT_ARGS,
)
from config_private import COMPARTMENT_OCID
from utils import get_console_logger

logger = get_console_logger()

db_manager = DatabaseManager(CONNECT_ARGS, logger)
llm_manager = LLMManager(
    MODEL_LIST, MODEL_ENDPOINTS, COMPARTMENT_OCID, TEMPERATURE, logger
)

# to get all the tables
PREFIX = "DH_C"

tables = db_manager.get_tables_list(PREFIX)

error_list = []

i = 0
for table in tqdm(tables):
    # sql alchemy use names in lowercase (?)
    include_tables = [table.lower()]

    print(include_tables)

    toolkit = SQLDatabaseToolkit(
        db=SQLDatabase(db_manager.engine, include_tables=include_tables),
        llm=llm_manager.llm_models[0],
    )

    raw_schema = toolkit.get_context()

    print(raw_schema)
    print(type(raw_schema))

    if "ERROR" in raw_schema["table_info"].upper():
        i += 1
        error_list.append(table)
        print("Errore: %s", table)

print(error_list)
