"""
TO test the AISQLAgent class
"""

from ai_sql_agent import AISQLAgent
from prompt_template import PROMPT_TEMPLATE
from config import MODEL_LIST, ENDPOINT, TEMPERATURE, EMBED_MODEL_NAME, CONNECT_ARGS
from config_private import COMPARTMENT_OCID

if __name__ == "__main__":
    # Configuration details

    # Initialize the agent, only once !!!
    ai_sql_agent = AISQLAgent(
        CONNECT_ARGS,
        MODEL_LIST,
        ENDPOINT,
        COMPARTMENT_OCID,
        EMBED_MODEL_NAME,
        TEMPERATURE,
        PROMPT_TEMPLATE,
    )

    # Some user requests to test on SH and AP_INVOICES
    user_requests = [
        "List the available tables",
        "List the top 10 sales by total amount, with product name, customer name, country name for sales in Europe",
        "Show me invoice 123456",
        "show me the list of first 10 professors teaching in the school",
    ]

    for user_request in user_requests:
        print("")
        print("User request: ", user_request)
        # Generate SQL query
        sql_query = ai_sql_agent.generate_sql_query(user_request)

        print("Generated SQL Query:")
        print(sql_query)
