"""
SQL Agent prototype v 0.9: UI

This version use the SchemaManager
"""

import streamlit as st

import matplotlib.pyplot as plt
from sqlalchemy import text

from langchain_community.embeddings import OCIGenAIEmbeddings
from database_manager import DatabaseManager
from llm_manager import LLMManager
from schema_manager import SchemaManager
from user_profile_manager import ProfileManager


from core_functions import (
    generate_sql_with_models,
    explain_response,
    extract_plot_code_from_response,
)
from prompt_template import PROMPT_TEMPLATE
from utils import get_console_logger
from config import (
    CONNECT_ARGS,
    ENABLE_AI_EXPLANATION,
    MODEL_LIST,
    ENDPOINT,
    TEMPERATURE,
    EMBED_MODEL_NAME,
)
from config import DEBUG
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


def create_schema_manager(_db_manager, _llm_manager):
    """
    Function to create and cache the LLM manager
    """
    embed_model = OCIGenAIEmbeddings(
        model_id=EMBED_MODEL_NAME,
        service_endpoint=ENDPOINT,
        compartment_id=COMPARTMENT_OCID,
    )
    schema_manager = SchemaManager(_db_manager, _llm_manager, embed_model, logger)

    if schema_manager is None:
        st.error("Error setting up SchemaManager")
        logger.error("Error setting up SchemaManager")
        st.stop()

    return schema_manager


def init_session(db_manager, llm_manager):
    """
    Init the session caching DB schema in session
    """
    if "schema_manager" not in st.session_state:
        logger.info("Reading DB schema info...")

        with st.spinner("Initialising Schema Manager..."):
            st.session_state.schema_manager = create_schema_manager(
                db_manager, llm_manager
            )


#
# Main
#

# Sidebar options for model selection
st.sidebar.title("Features selection")

CHECK_AI_EXPL_DISABLED = not ENABLE_AI_EXPLANATION

check_enable_ai_expl = st.sidebar.checkbox(
    "Enable AI explanation", disabled=CHECK_AI_EXPL_DISABLED
)

check_enable_plot = st.sidebar.checkbox("Enable plot")

# to enable RBAC
check_enable_rbac = st.sidebar.checkbox("Enable RBAC")

if check_enable_rbac:
    # enabled RBAC read group_id
    group_id = st.sidebar.number_input(
        "User group id:", min_value=1, max_value=10, step=1
    )
    # here we set the user profile
    user_profile = ProfileManager(user_group_id=group_id)
else:
    # No RBAC
    user_profile = None
    group_id = None


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

    # 1. Run the LLM to generate the SQL query and cleans it (remove initial sql, final ;..)
    # added support for RBAC
    if user_profile is not None:
        if user_profile.get_user_group_id() is not None:
            group_id = user_profile.get_user_group_id()

    # gest restricteed schema for the given user_query
    restricted_schema = st.session_state.schema_manager.get_restricted_schema(
        user_query
    )

    cleaned_query = generate_sql_with_models(
        user_query,
        restricted_schema,
        db_manager,
        llm_manager,
        PROMPT_TEMPLATE,
        group_id,
    )

    if len(cleaned_query) > 0:
        st.write(f"**Generated SQL Query: {cleaned_query}**")

        # Execute the SQL query
        try:
            with db_manager.engine.connect() as connection:
                # 1. execute query
                logger.info("")
                logger.info("Executing query...")

                logger.info("User group id: %s", group_id)

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

                            # 3. run code for plot
                            if check_enable_plot:
                                plot_code = extract_plot_code_from_response(
                                    ai_explanation
                                )

                                # execute and show in streamlit
                                exec(plot_code)
                                st.pyplot(plt)

                except Exception as e:
                    logger.error("Error interpreting results: %s", e)
                    st.error(f"Error interpreting results: {e}")

        except Exception as e:
            logger.error("UI: Error executing SQL query: %s", e)
            st.error(f"Error executing SQL query: {e}")

    else:
        st.error("Sorry, could not generate a valid SQL query from the response.")
        logger.error("Sorry, could not generate a valid SQL query from the response.")
