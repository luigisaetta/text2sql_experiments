"""
File name: batch_load_vector_store_23ai.py
Author: Luigi Saetta
Date last modified: 2024-10-21
Python Version: 3.11

Description:
    Encapsulate the code to load the metadata repository
    and the Vector Store
    Load 23AI Vector Store for restricted schema

    This is the script to be used to do the first/complete load of the SCHEMA_VECTORS.
    It will drop and reload the collection.

Inspired by:
   
Usage:
    Import this module into other scripts to use its functions. 
    Example:

Dependencies:
    langChain

License:
    This code is released under the MIT License.

Notes:
    This is a part of a set of demos showing how to build a SQL Agent
    for Text2SQL taks

Warnings:
    This module is in development, may change in future versions.
"""

from langchain_community.embeddings import OCIGenAIEmbeddings
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

logger.info("")
logger.info("")

# with these we connect to the data schema
db_manager = DatabaseManager(CONNECT_ARGS, logger)
llm_manager = LLMManager(
    MODEL_LIST, MODEL_ENDPOINTS, COMPARTMENT_OCID, TEMPERATURE, logger
)

embed_model = OCIGenAIEmbeddings(
    auth_type=AUTH_TYPE,
    model_id=EMBED_MODEL_NAME,
    service_endpoint=EMBED_ENDPOINT,
    compartment_id=COMPARTMENT_OCID,
)


logger.info("")
logger.info("Loading Schema Manager...")

# schema manager encapsulate the connection to vector store db
schema_manager = SchemaManager23AI(db_manager, llm_manager, embed_model, logger)

# read the data from the data DB (using db_manager)
# generate for each table a summary using LLM
# embeds summary and store summary + embeddings + metadata
# in 23AI Vector Store
schema_manager.init_schema_manager()

logger.info("Loaded !!!")
logger.info("")

# do a test
logger.info("Quick test...")
logger.info("")
USER_QUERY = "list the top 5 sales by total amount"

logger.info("User query: %s", USER_QUERY)
logger.info("")

# get the schema for the user request
SCHEMA = schema_manager.get_restricted_schema(USER_QUERY)

logger.info("Schema:")
logger.info(SCHEMA)
