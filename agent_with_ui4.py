"""
SQL Agent prototype v 0.8: UI
"""

import streamlit as st

from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI

from sqlalchemy import text

from core_functions import (
    create_db_engine,
    get_formatted_schema,
    rephrase_response,
    generate_sql_query_with_models,
)
from utils import get_console_logger

from config_private import COMPARTMENT_OCID, ENDPOINT, MODEL_LIST, ENABLE_AI_EXPLANATION

logger = get_console_logger()


@st.cache_resource
def create_cached_db_engine():
    """
    Function to create and cache the database connection
    """
    try:
        _engine = create_db_engine()

        return _engine
    except Exception as e:
        st.error(f"Error setting up SQLDatabase: {e}")
        logger.error("Error setting up SQLDatabase %s", e)
        st.stop()


def init_session():
    """
    Init the session caching DB schema in session
    """
    if "schema" not in st.session_state:
        logger.info("Reading DB schema info...")

        with st.spinner("Getting schema information..."):
            # putting schema in the session we avoid it is
            # read for every request
            st.session_state.schema = get_formatted_schema(engine, model_list[0])


#
# Main
#

# Sidebar options for model selection
st.sidebar.title("Model Selection")

selected_model = st.sidebar.selectbox("Choose an LLM model:", MODEL_LIST)

# Set up the LLM model list
model_list = [
    ChatOCIGenAI(
        # 0 is currently llama3-70B
        model_id=model,
        service_endpoint=ENDPOINT,
        compartment_id=COMPARTMENT_OCID,
        model_kwargs={"temperature": 0, "max_tokens": 2048},
    )
    for model in MODEL_LIST
]

# Create the database engine once and cache it
engine = create_cached_db_engine()

# here we get the schema and cache in session
init_session()

# Streamlit UI
st.title("Oracle GenAI SQL Chat Interface")

# Create a form to handle the input and button together
with st.form(key="query_form"):
    # enlarged now it is multiline
    user_query = st.text_area("Enter your query:", "", height=100)
    submit_button = st.form_submit_button(label="Run Query")

if submit_button and user_query:
    # Show a status message immediately
    st.info("Processing your request...")

    # Run the LLM to generate the SQL query and cleans it (remove initial sql, final ;..)
    cleaned_query = generate_sql_query_with_models(
        user_query, st.session_state.schema, engine, model_list, verbose=True
    )

    if len(cleaned_query) > 0:
        st.write(f"**Generated SQL Query: {cleaned_query}**")

        # Execute the SQL query
        try:
            with engine.connect() as connection:
                # 1. execute query
                logger.info("")
                logger.info("Executing query...")

                # now we have two separate spinner
                with st.spinner("Fetching details from database..."):
                    result = connection.execute(text(cleaned_query))
                    rows = result.fetchall()

                    logger.info("Found %s rows..", len(rows))

                st.write("**Query Results:**")
                st.table(rows)

                # 2. analyze results with AI
                try:
                    if ENABLE_AI_EXPLANATION:
                        logger.info("AI interpreting response...")
                        original_response = f"""I asked a question {user_query}
                                and the response from database was {rows}."""

                        with st.spinner("Interpreting results with AI.."):
                            rephrased_response = rephrase_response(
                                original_response, model_list[0]
                            )

                            st.write("**Response:**")
                            st.write(rephrased_response)

                except Exception as e:
                    logger.error("Error interpreting results: %s", e)
                    st.error(f"Error interpreting results: {e}")

        except Exception as e:
            logger.error("Error executing SQL query: %s", e)
            st.error(f"Error executing SQL query: {e}")

    else:
        st.error("Sorry, could not generate a valid SQL query from the response.")
        logger.error("Sorry, could not generate a valid SQL query from the response.")
