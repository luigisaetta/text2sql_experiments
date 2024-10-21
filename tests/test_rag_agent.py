"""
To test AI RAG Agent
"""

from ai_rag_agent import AIRAGAgent

from config import (
    CONNECT_ARGS_VECTOR,
    MODEL_LIST,
    MODEL_ENDPOINTS,
    EMBED_MODEL_NAME,
    EMBED_ENDPOINT,
)
from config_private import COMPARTMENT_OCID

from utils import get_console_logger

logger = get_console_logger()

logger.info("")
logger.info("Initialising RAG Agent...")
logger.info("")

agent = AIRAGAgent(
    CONNECT_ARGS_VECTOR,
    MODEL_LIST,
    MODEL_ENDPOINTS,
    COMPARTMENT_OCID,
    EMBED_MODEL_NAME,
    EMBED_ENDPOINT,
    0.1,
    logger,
)

QUESTION = "What are the current policies regarding maternity leave?"
# QUESTION = "List the public holydays in UAE"

# response = agent.get_relevant_docs(QUESTION)

# for doc in response:
#  logger.info(doc.page_content)
#   logger.info("")
#    logger.info("")

response = agent.answer(QUESTION)

logger.info("")
logger.info(QUESTION)
logger.info("Answer: %s", response.content)
