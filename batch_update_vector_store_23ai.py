"""
Batch to update Vector Store only for some tables

You need to give the list of the names of the tables
"""

from oci_cohere_embeddings_utils import OCIGenAIEmbeddingsWithBatch
from database_manager import DatabaseManager
from llm_manager import LLMManager
from schema_manager_23ai import SchemaManager23AI
from utils import get_console_logger
from config import (
    CONNECT_ARGS,
    MODEL_LIST,
    MODEL_ENDPOINTS,
    TEMPERATURE,
    EMBED_MODEL_NAME,
    EMBED_ENDPOINT,
)
from config_private import COMPARTMENT_OCID

tables_list = ["APPO", "AP_INVOICES", "EMPLOYEES"]

#
# Main
#
logger = get_console_logger()

logger.info("")
logger.info("")
logger.info("Update Vector Store for selected tables:")
logger.info(tables_list)
logger.info("")

# with these we connect to the data schema
db_manager = DatabaseManager(CONNECT_ARGS, logger)
llm_manager = LLMManager(
    MODEL_LIST, MODEL_ENDPOINTS, COMPARTMENT_OCID, TEMPERATURE, logger
)

embed_model = OCIGenAIEmbeddingsWithBatch(
    model_id=EMBED_MODEL_NAME,
    service_endpoint=EMBED_ENDPOINT,
    compartment_id=COMPARTMENT_OCID,
)


logger.info("")
logger.info("Loading Schema Manager...")
logger.info("")

# schema manager encapsulate the connection to vector store db
schema_manager = SchemaManager23AI(db_manager, llm_manager, embed_model, logger)

# update the record in the VECTOR schema only for tables in the list
schema_manager.update_schema_manager(tables_list)
