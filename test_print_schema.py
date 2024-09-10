"""
Print the current schema
"""

from core_functions import get_formatted_schema

from database_manager import DatabaseManager
from llm_manager import LLMManager

from utils import get_console_logger
from config import CONNECT_ARGS, MODEL_LIST, ENDPOINT, TEMPERATURE
from config_private import COMPARTMENT_OCID

logger = get_console_logger()

db_manager = DatabaseManager(CONNECT_ARGS, logger)
llm_manager = LLMManager(MODEL_LIST, ENDPOINT, COMPARTMENT_OCID, TEMPERATURE, logger)

engine = db_manager.engine
# 0 is llama3-70B
llm1 = llm_manager.llm_models[0]

SCHEMA = get_formatted_schema(engine, llm1)

print(SCHEMA)
