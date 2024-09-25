"""
Utility to check that the syntax of SQL query in few shot examples is correct
"""

from database_manager import DatabaseManager
from utils import get_console_logger
from config import CONNECT_ARGS
from examples_4_prompt import EXAMPLES

logger = get_console_logger()

logger.info("")
logger.info("Check SQL syntax for all SQL query in examples_4_prompt")
logger.info("")

db_manager = DatabaseManager(CONNECT_ARGS, logger)

# start reading list of SQL
lines = EXAMPLES.splitlines()

# List to memorize all sql queries
sql_queries = []

current_sql_query = []
is_sql_query = False

for line in lines:
    # If the line starts with "SQL Query:", a new query begins
    if line.startswith("SQL Query:"):
        if current_sql_query:  # if there  is already a sql_query accumulated, save it
            sql_queries.append(" ".join(current_sql_query).strip())
        # Inizia una nuova query
        current_sql_query = [line.replace("SQL Query:", "").strip()]
        is_sql_query = True
    elif line.startswith("User Query:"):
        # if we find a new line with "User Query" previous SQL query has completed
        if current_sql_query:
            sql_queries.append(" ".join(current_sql_query).strip())
            current_sql_query = []
        is_sql_query = False
    elif is_sql_query:
        current_sql_query.append(line.strip())

# Add last sql query if present
if current_sql_query:
    sql_queries.append(" ".join(current_sql_query).strip())

logger.info("")
logger.info("")
for query in sql_queries:
    print(query)

    IS_OK = db_manager.test_query_syntax(query)

    if IS_OK:
        logger.info("SQL Query sintax OK !")
    logger.info("")
