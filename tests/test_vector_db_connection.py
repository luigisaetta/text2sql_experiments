"""
Test connction to Vector Store
"""

from langchain_community.embeddings import OCIGenAIEmbeddings

from schema_manager_23ai import SchemaManager23AI
from database_manager import DatabaseManager
from llm_manager import LLMManager
from config import (
    CONNECT_ARGS,
    MODEL_LIST,
    MODEL_ENDPOINTS,
    TEMPERATURE,
    EMBED_MODEL_NAME,
    EMBED_ENDPOINT,
)
from config_private import COMPARTMENT_OCID
from utils import get_console_logger

logger = get_console_logger()

db_manager = DatabaseManager(CONNECT_ARGS, logger)
llm_manager = LLMManager(
    MODEL_LIST, MODEL_ENDPOINTS, COMPARTMENT_OCID, TEMPERATURE, logger
)

embed_model = OCIGenAIEmbeddings(
    model_id=EMBED_MODEL_NAME,
    service_endpoint=EMBED_ENDPOINT,
    compartment_id=COMPARTMENT_OCID,
)

logger.info("")
logger.info("Loading Schema Manager...")

schema_manager = SchemaManager23AI(db_manager, llm_manager, embed_model, logger)

conn = schema_manager._get_vector_db_connection()

if conn.is_healthy():
    logger.info("")
    logger.info("Connection to VECTOR STORE OK...")
    logger.info("")
