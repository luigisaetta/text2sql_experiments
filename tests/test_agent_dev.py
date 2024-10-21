"""
This is  a test client for Development SQL Agent Alfa
"""

import oci
from oci.generative_ai_agent_runtime import GenerativeAiAgentRuntimeClient
from oci.generative_ai_agent_runtime.models.chat_details import ChatDetails
from oci.retry import NoneRetryStrategy

from database_manager import DatabaseManager
from config import CONNECT_ARGS
from utils import get_console_logger

# configs
CONFIG_PROFILE = "DEFAULT"

# sessionless agent endpoint.
AGENT_ENDPOINT_ID = "ocid1.genaiagentendpoint.oc1.us-chicago-1.amaaaaaa2xxap7ya7msz4izgftuealp3xerc2skhbiwv3p5px7qnypuyyeca"
# Service endpoint
ENDPOINT = "https://agent-runtime.generativeai.us-chicago-1.oci.oraclecloud.com"

logger = get_console_logger()

# file with the prompt
with open("prompt_for_agent_dev.txt", "r", encoding="UTF-8") as file:
    prompt = file.read()

# now battery of test using SH schema:
TESTS_FILE_NAME = "testsh50.txt"

# read the file with users requests
with open(TESTS_FILE_NAME, "r", encoding="UTF-8") as file:
    USER_QUERIES = [linea.strip() for linea in file]

config = oci.config.from_file("~/.oci/config", CONFIG_PROFILE)

oci_client = GenerativeAiAgentRuntimeClient(
    config=config,
    service_endpoint=ENDPOINT,
    retry_strategy=NoneRetryStrategy(),
    timeout=(10, 240),
)

# to check the query generated against DB
db_manager = DatabaseManager(CONNECT_ARGS, logger)

n_ok = 0

for i, question in enumerate(USER_QUERIES):

    request = prompt + question + "\nOracle SQL:"
    chat_details = ChatDetails(user_message=request, should_stream=False)

    chat_response = oci_client.chat(AGENT_ENDPOINT_ID, chat_details)

    # extract query generated
    sql_query = chat_response.data.message.content.text

    # Print result
    logger.info("-----------------------------------")
    logger.info("%d User query: %s", i + 1, question)
    logger.info("")

    # check if query can be executed
    # log errors if any
    if db_manager.test_query_syntax(sql_query):
        n_ok += 1
        logger.info("OK")
    else:
        logger.info("")

    logger.info("-----------------------------------")

logger.info("")
logger.info("Results:")
logger.info("N. OK: %s", n_ok)
logger.info("N. User Query: %s", len(USER_QUERIES))
