""""
Load 23AI Vector Store for restricted schema
"""

from langchain_community.embeddings import OCIGenAIEmbeddings

from database_manager import DatabaseManager
from llm_manager import LLMManager
from schema_manager_23ai import SchemaManager23AI
from utils import get_console_logger
from config import CONNECT_ARGS, MODEL_LIST, ENDPOINT, TEMPERATURE, EMBED_MODEL_NAME
from config_private import COMPARTMENT_OCID


logger = get_console_logger()

logger.info("")
logger.info("")

# with these we connect to the data schema
db_manager = DatabaseManager(CONNECT_ARGS, logger)
llm_manager = LLMManager(MODEL_LIST, ENDPOINT, COMPARTMENT_OCID, TEMPERATURE, logger)

embed_model = OCIGenAIEmbeddings(
    model_id=EMBED_MODEL_NAME,
    service_endpoint=ENDPOINT,
    compartment_id=COMPARTMENT_OCID,
)

llm1 = llm_manager.llm_models[0]

logger.info("")
logger.info("Loading Schema Manager...")

schema_manager = SchemaManager23AI(db_manager, llm_manager, embed_model, logger)

# reload the data
schema_manager.init_schema_manager()

# do a test
user_query = "list the top 5 sales by total amount"

schema = schema_manager.get_restricted_schema(user_query)

logger.info("User query: %s", user_query)
logger.info("")
logger.info("Schema:")
logger.info(schema)
