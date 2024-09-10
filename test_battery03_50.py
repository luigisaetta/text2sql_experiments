"""
Battery of test03

These are tests generated by GPT-O

This script tests only that SQL syntax is correct. 
Ok if SQL can be executed on Oracle DB
"""

from tqdm import tqdm

from database_manager import DatabaseManager
from llm_manager import LLMManager

from core_functions import (
    get_formatted_schema,
    generate_sql_with_models,
)
from prompt_template import PROMPT_TEMPLATE
from utils import get_console_logger
from config import CONNECT_ARGS, MODEL_LIST, ENDPOINT, TEMPERATURE
from config_private import DB_USER, COMPARTMENT_OCID

# SH schema
# TESTS_FILE_NAME = "testsh50.txt"
TESTS_FILE_NAME = "testhr30.txt"

# Leggi il file riga per riga e carica ogni riga in una lista
with open(TESTS_FILE_NAME, "r", encoding="UTF-8") as file:
    USER_QUERIES = [linea.strip() for linea in file]


logger = get_console_logger()

logger.info("")
logger.info("Testing on schema: %s", DB_USER)
logger.info("")

db_manager = DatabaseManager(CONNECT_ARGS, logger)
llm_manager = LLMManager(MODEL_LIST, ENDPOINT, COMPARTMENT_OCID, TEMPERATURE, logger)

engine = db_manager.engine
# 0 is llama3-70B
llm1 = llm_manager.llm_models[0]

SCHEMA = get_formatted_schema(engine, llm1)

N_QUERIES = 0
N_OK = 0

for user_query in tqdm(USER_QUERIES):
    N_QUERIES += 1

    sql_query = generate_sql_with_models(
        user_query, SCHEMA, db_manager, llm_manager, PROMPT_TEMPLATE
    )

    # generate with pairs check the sintax
    # if sintax is wrong return empty string
    if len(sql_query) > 0:
        N_OK += 1

print("")
print("Summary of Test results:")
print("Number of queries: ", N_QUERIES)
print("Number of test ok: ", N_OK)
