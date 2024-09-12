"""
SQL Agent prototype v 0.8: UI
"""

import streamlit as st


from sqlalchemy import text

from database_manager import DatabaseManager
from llm_manager import LLMManager

from core_functions import (
    get_formatted_schema,
    generate_sql_with_models,
    explain_response,
)
from prompt_template import PROMPT_TEMPLATE
from utils import get_console_logger
from config import (
    CONNECT_ARGS,
    ENABLE_AI_EXPLANATION,
    MODEL_LIST,
    ENDPOINT,
    TEMPERATURE,
)
from config_private import COMPARTMENT_OCID

logger = get_console_logger()


@st.cache_resource
def create_cached_db_manager():
    """
    Function to create and cache the database manager
    """
    db_manager = DatabaseManager(CONNECT_ARGS, logger)

    if db_manager is None:
        st.error("Error setting up DBManager")
        logger.error("Error setting up DBManager")
        st.stop()

    return db_manager


@st.cache_resource
def create_cached_llm_manager():
    """
    Function to create and cache the LLM manager
    """
    llm_manager = LLMManager(
        MODEL_LIST, ENDPOINT, COMPARTMENT_OCID, TEMPERATURE, logger
    )

    if llm_manager is None:
        st.error("Error setting up LLMManager")
        logger.error("Error setting up LLMManager")
        st.stop()

    return llm_manager


def init_session(db_manager, llm_manager):
    """
    Init the session caching DB schema in session
    """
    if "schema" not in st.session_state:
        logger.info("Reading DB schema info...")

        with st.spinner("Getting schema information..."):
            # putting schema in the session we avoid it is
            # read for every request
            engine = db_manager.engine
            llm1 = llm_manager.llm_models[0]

            st.session_state.schema = get_formatted_schema(engine, llm1)


#
# Main
#

# Sidebar options for model selection
st.sidebar.title("Features selection")

CHECK_AI_EXPL_DISABLED = not ENABLE_AI_EXPLANATION

check_enable_ai_expl = st.sidebar.checkbox(
    "Enable AI explanation", disabled=CHECK_AI_EXPL_DISABLED
)

# Create the database engine once and cache it
db_manager = create_cached_db_manager()

llm_manager = create_cached_llm_manager()

# here we get the schema and cache in session
init_session(db_manager, llm_manager)

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
    cleaned_query = generate_sql_with_models(
        user_query, st.session_state.schema, db_manager, llm_manager, PROMPT_TEMPLATE
    )

    if len(cleaned_query) > 0:
        st.write(f"**Generated SQL Query: {cleaned_query}**")

        # Execute the SQL query
        try:
            with db_manager.engine.connect() as connection:
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
                            llm2 = llm_manager.get_llm_models()[1]

                            ai_explanation = explain_response(
                                # user_query: initial request from user
                                # rows: SQL results
                                # uses c-r-plus (model1)
                                user_query,
                                rows,
                                llm2,
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
