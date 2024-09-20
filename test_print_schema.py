"""
Print the current schema
"""

from database_manager import DatabaseManager
from llm_manager import LLMManager
from core_functions import get_formatted_schema
from utils import get_console_logger
from config import CONNECT_ARGS, MODEL_LIST, MODEL_ENDPOINTS, TEMPERATURE
from config_private import COMPARTMENT_OCID

logger = get_console_logger()

db_manager = DatabaseManager(CONNECT_ARGS, logger)
llm_manager = LLMManager(MODEL_LIST, MODEL_ENDPOINTS, COMPARTMENT_OCID, TEMPERATURE, logger)

SCHEMA = get_formatted_schema(
    db_manager.engine,
    # 0 is Llama3
    llm_manager.llm_models[0],
)

print(SCHEMA)
