"""
Test Table Summary

16/09: modified to use 23AI VS
19/09: modified to use AISQLAgent class
"""

from ai_sql_agent import AISQLAgent
from utils import get_console_logger
from prompt_template import PROMPT_TEMPLATE

from config import (
    CONNECT_ARGS,
    MODEL_LIST,
    ENDPOINT,
    TEMPERATURE,
    EMBED_MODEL_NAME,
)
from config_private import COMPARTMENT_OCID


#
# Main
#
logger = get_console_logger()

# init SQL Agent only once
ai_sql_agent = AISQLAgent(
    CONNECT_ARGS,
    MODEL_LIST,
    ENDPOINT,
    COMPARTMENT_OCID,
    EMBED_MODEL_NAME,
    TEMPERATURE,
    PROMPT_TEMPLATE,
)

# now battery of test using SH schema:
TESTS_FILE_NAME = "testsh50.txt"
# TESTS_FILE_NAME = "testhr30.txt"
# TESTS_FILE_NAME = "testhr_problems.txt"
# TESTS_FILE_NAME = "testsh30_ita.txt"

# read the file with users requests
with open(TESTS_FILE_NAME, "r", encoding="UTF-8") as file:
    USER_QUERIES = [linea.strip() for linea in file]

logger.info("")
logger.info("Starting battery of test:")
logger.info("")

# to limit the number of test
TO_TEST = 30
N_OK = 0

for query in USER_QUERIES[:TO_TEST]:
    logger.info("User query: %s", query)

    # generate SQL
    sql_query = ai_sql_agent.generate_sql_query(query)

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
