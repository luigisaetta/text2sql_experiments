"""
Test Table Summary

16/09: modified to use 23AI VS
"""

from langchain_community.embeddings import OCIGenAIEmbeddings

from database_manager import DatabaseManager
from llm_manager import LLMManager
from schema_manager_23ai import SchemaManager23AI
from core_functions import generate_sql_with_models
from utils import get_console_logger
from prompt_template import PROMPT_TEMPLATE

from config import (
    CONNECT_ARGS,
    MODEL_LIST,
    ENDPOINT,
    TEMPERATURE,
    DEBUG,
    EMBED_MODEL_NAME,
)
from config_private import COMPARTMENT_OCID


#
# Main
#
logger = get_console_logger()

db_manager = DatabaseManager(CONNECT_ARGS, logger)
llm_manager = LLMManager(MODEL_LIST, ENDPOINT, COMPARTMENT_OCID, TEMPERATURE, logger)

embed_model = OCIGenAIEmbeddings(
    model_id=EMBED_MODEL_NAME,
    service_endpoint=ENDPOINT,
    compartment_id=COMPARTMENT_OCID,
)

logger.info("")
logger.info("Loading Schema Manager...")

schema_manager = SchemaManager23AI(db_manager, llm_manager, embed_model, logger)

# now battery of test using SH schema:

TESTS_FILE_NAME = "testsh50.txt"
# TESTS_FILE_NAME = "testhr30.txt"

# read the file with users requests
with open(TESTS_FILE_NAME, "r", encoding="UTF-8") as file:
    USER_QUERIES = [linea.strip() for linea in file]

logger.info("")
logger.info("Starting battery of test:")
logger.info("")

# to limit the number of test
TO_TEST = 50
N_OK = 0

for query in USER_QUERIES[:TO_TEST]:
    logger.info("User query: %s", query)

    RESTRICTED_SCHEMA = schema_manager.get_restricted_schema(query)

    if DEBUG:
        logger.info(RESTRICTED_SCHEMA)

    # generate SQL
    sql_query = generate_sql_with_models(
        query, RESTRICTED_SCHEMA, db_manager, llm_manager, PROMPT_TEMPLATE
    )

    # generate_sql_with_model check the syntax
    # if syntax is wrong return empty string
    if len(sql_query) > 0:
        # ok generated
        N_OK += 1
        logger.info("")
        logger.info("Query Generation OK !!!")
    else:
        logger.error("Query Generation KO !!!")

    logger.info("")
    logger.info("")

print("")
print("Summary of Test results:")
print("Number of queries: ", len(USER_QUERIES[:TO_TEST]))
print("Number of test ok: ", N_OK)
print("")
