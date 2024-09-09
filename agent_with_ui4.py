"""
SQL Agent prototype v 0.8: UI
"""

import streamlit as st


from sqlalchemy import text

from core_functions import (
    create_db_engine,
    get_formatted_schema,
    generate_sql_query_with_models,
    get_chat_models,
    explain_response,
)
from utils import get_console_logger
from config import ENABLE_AI_EXPLANATION

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
st.sidebar.title("Features selection")

CHECK_AI_EXPL_DISABLED = not ENABLE_AI_EXPLANATION

check_enable_ai_expl = st.sidebar.checkbox(
    "Enable AI explanation", disabled=CHECK_AI_EXPL_DISABLED
)

# Set up the LLM model list
model_list = get_chat_models()

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
        user_query, st.session_state.schema, engine, model_list
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
                    if check_enable_ai_expl:
                        logger.info("AI interpreting response...")

                        with st.spinner("Interpreting results with AI..."):
                            # 9/9 (LS) changed prompt and model, now r-plus
                            ai_explanation = explain_response(
                                # user_query: initial request from user
                                # rows: SQL results
                                # uses c-r-plus (model1)
                                user_query,
                                rows,
                                model_list[1],
                            )

                            st.write("**AI explanation:**")
                            st.write(ai_explanation)

                except Exception as e:
                    logger.error("Error interpreting results: %s", e)
                    st.error(f"Error interpreting results: {e}")

        except Exception as e:
            logger.error("Error executing SQL query: %s", e)
            st.error(f"Error executing SQL query: {e}")

    else:
        st.error("Sorry, could not generate a valid SQL query from the response.")
        logger.error("Sorry, could not generate a valid SQL query from the response.")
