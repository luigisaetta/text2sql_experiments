"""
Test the router
"""

from llm_manager import LLMManager
from router import Router
from utils import get_console_logger
from config import MODEL_LIST, MODEL_ENDPOINTS, TEMPERATURE
from config_private import COMPARTMENT_OCID

logger = get_console_logger()

llm_manager = LLMManager(
    MODEL_LIST, MODEL_ENDPOINTS, COMPARTMENT_OCID, TEMPERATURE, logger
)

router = Router(llm_manager)

# now battery of test using SH schema:
# TESTS_FILE_NAME = "testsh50.txt"
# TESTS_FILE_NAME = "testhr30.txt"
# TESTS_FILE_NAME = "testhr_problems.txt"
TESTS_FILE_NAME = "testsh30_ita.txt"
# TESTS_FILE_NAME = "test_hospital.txt"
# TESTS_FILE_NAME = "test_routing.txt"

# read the file with users requests
with open(TESTS_FILE_NAME, "r", encoding="UTF-8") as file:
    USER_QUERIES = [linea.strip() for linea in file]

logger.info("")
logger.info("Test routing:")
logger.info("")

for user_query in USER_QUERIES:
    classification = router.classify(user_query)

    print("User query:", user_query)
    print(classification)
    print("")
