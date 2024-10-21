"""
Print the current schema
"""

from oci_cohere_embeddings_utils import OCIGenAIEmbeddingsWithBatch
from database_manager import DatabaseManager
from llm_manager import LLMManager
from schema_manager_23ai import SchemaManager23AI
from utils import get_console_logger
from config import (
    AUTH_TYPE,
    CONNECT_ARGS,
    MODEL_LIST,
    MODEL_ENDPOINTS,
    TEMPERATURE,
    EMBED_MODEL_NAME,
    EMBED_ENDPOINT,
)
from config_private import COMPARTMENT_OCID

logger = get_console_logger()

# with these we connect to the data schema
db_manager = DatabaseManager(CONNECT_ARGS, logger)
llm_manager = LLMManager(
    MODEL_LIST, MODEL_ENDPOINTS, COMPARTMENT_OCID, TEMPERATURE, logger
)

embed_model = OCIGenAIEmbeddingsWithBatch(
    auth_type=AUTH_TYPE,
    model_id=EMBED_MODEL_NAME,
    service_endpoint=EMBED_ENDPOINT,
    compartment_id=COMPARTMENT_OCID,
)


logger.info("")
logger.info("Loading Schema Manager...")

# schema manager encapsulate the connection to vector store db
schema_manager = SchemaManager23AI(db_manager, llm_manager, embed_model, logger)

TESTS_FILE_NAME = "test_absences.txt"

# read the file with users requests
with open(TESTS_FILE_NAME, "r", encoding="UTF-8") as file:
    USER_QUERIES = [linea.strip() for linea in file]

for user_query in USER_QUERIES:
    restricted_schema = schema_manager.get_restricted_schema(user_query)

    logger.info(user_query)
    logger.info("Schema len: %5d char.", len(restricted_schema))
    logger.info("")
