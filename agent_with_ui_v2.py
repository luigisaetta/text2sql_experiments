"""
SQL Agent prototype v 0.9: UI

This version use the SchemaManager
"""

import streamlit as st

import matplotlib.pyplot as plt
from sqlalchemy import text

from database_manager import DatabaseManager
from llm_manager import LLMManager
from ai_sql_agent import AISQLAgent
from user_profile_manager import ProfileManager


from core_functions import (
    explain_response,
    extract_plot_code_from_response,
)
from prompt_template import PROMPT_TEMPLATE
from utils import get_console_logger
from config import (
    CONNECT_ARGS,
    ENABLE_AI_EXPLANATION,
    MODEL_LIST,
    MODEL_ENDPOINTS,
    TEMPERATURE,
    EMBED_MODEL_NAME,
    EMBED_ENDPOINT,
    INDEX_MODEL_FOR_EXPLANATION,
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
        MODEL_LIST, MODEL_ENDPOINTS, COMPARTMENT_OCID, TEMPERATURE, logger
    )

    if llm_manager is None:
        st.error("Error setting up LLMManager")
        logger.error("Error setting up LLMManager")
        st.stop()

    return llm_manager


def init_session():
    """
    Init the session caching DB schema in session
    """
    if "sql_agent" not in st.session_state:
        logger.info("Initialising SQL Agent...")

        with st.spinner("Initialising SQL Agent..."):
            st.session_state.sql_agent = AISQLAgent(
                CONNECT_ARGS,
                MODEL_LIST,
                MODEL_ENDPOINTS,
                COMPARTMENT_OCID,
                EMBED_MODEL_NAME,
                EMBED_ENDPOINT,
                TEMPERATURE,
                PROMPT_TEMPLATE,
            )
        logger.info("Ready !!!")
        logger.info("")

    if "user_query" not in st.session_state:
        st.session_state.user_query = ""


def abbreviate_question(question, max_length=40):
    """
    Abbreviate the sample question for better presentation in UI
    """
    if len(question) > max_length:
        return question[:max_length] + "..."
    return question


#
# Main
#
# Streamlit UI
st.title("Oracle SQL Agent V2.1")

# section to handle sample question
st.sidebar.title("Sample questions")

# per commentare tutte insieme CMd + K, cmd +C
# sample_questions = [
#    "What is the total number of employees in the company as of today?",
#    "Can you show me a list of all departments along with the headcount in each department?",
#    "Retrieve the product names and the total amount sold for each product.",
#    "Which employees have joined the company in 2018, and what are their respective departments?",
#    """How many products have been sold in the last 30 days,
# categorized by region and product type?""",
# ]

# for e-biz
sample_questions = [
    "show all the distinct absence types that have been reported by employee",
    "show distinct absence types and the number of employees who reported them in 2017",
    "show all the employees names that have reported absence type name like 'Sick%'.",
    """show all the employee name that have reported absence type like 'Sick%' 
and the total number of hours reported. Order by number of hours descending""",
    """For every department shows the department name, the absence type name 
and total number of hour reported""",
    """show the names of all employees who registered absences started in 2017 
and the total hours for each absence type name""",
    "show all the employee located in US who have reported absences in 2017",
]
# Create abbreviated versions of the sample questions for the sidebar
abbreviated_questions = [abbreviate_question(q) for q in sample_questions]

# Add the radio buttons to the sidebar with abbreviated questions
selected_abbreviation = st.sidebar.radio("Choose a question:", abbreviated_questions)

# Find the full question corresponding to the selected abbreviation
selected_question = sample_questions[abbreviated_questions.index(selected_abbreviation)]

if selected_question:
    st.session_state.user_query = (
        selected_question  # Update session state with selected question
    )

# Sidebar options for features selection
st.sidebar.title("Features selection")

CHECK_AI_EXPL_DISABLED = not ENABLE_AI_EXPLANATION

check_show_sql = st.sidebar.checkbox("Show SQL")

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

# here we get the sql_agent in session
init_session()


# Create a form to handle the input and button together
with st.form(key="query_form"):
    # enlarged now it is multiline
    user_query = st.text_area(
        "Enter your query:", st.session_state.user_query, height=100
    )
    submit_button = st.form_submit_button(label="Run Query")

if submit_button and user_query:
    # Show a status message immediately
    st.info("Processing your request...")

    # 1. Run the LLM to generate the SQL query and cleans it (remove initial sql, final ;..)
    # added support for RBAC
    if user_profile is not None:
        if user_profile.get_user_group_id() is not None:
            group_id = user_profile.get_user_group_id()

    cleaned_query = st.session_state.sql_agent.generate_sql_query(
        user_query, user_group_id=group_id
    )

    if len(cleaned_query) > 0:
        if check_show_sql:
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
                            # 19/9 change to llama 3.1 405 in chicago
                            llm_e = llm_manager.get_llm_models()[
                                INDEX_MODEL_FOR_EXPLANATION
                            ]

                            ai_explanation = explain_response(
                                # user_query: initial request from user
                                # rows: SQL results
                                # uses c-r-plus (model1)
                                user_query,
                                rows,
                                llm_e,
                            )

                            st.write("**AI explanation:**")
                            st.write(ai_explanation)

                            # 3. run code for plot
                            if check_enable_plot:
                                plot_code = extract_plot_code_from_response(
                                    ai_explanation
                                )

                                # execute and show in streamlit
                                if plot_code is not None and len(plot_code) > 0:
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
