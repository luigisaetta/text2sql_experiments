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
        "give me examples of questions I can ask about our data",
        "List the top 10 sales by total amount, with product name, customer name, country name for sales in Europe",
        "Show me invoice 123456",
        "List all the departments with the number of empoyee for departments",
    ]

    for user_request in user_requests:
        print("")
        print("User request: ", user_request)
        # Generate SQL query
        # not using RBAC
        sql_query = ai_sql_agent.generate_sql_query(user_request, user_group_id=None)

        print("Generated SQL Query:")
        print(sql_query)
