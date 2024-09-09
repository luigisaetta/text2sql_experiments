"""
SQL agent core functions

This code comes from an initial work done by A. Panda, then we have added
several contributions to help increase accuracy
"""

import re

from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.prompts import PromptTemplate

from sqlalchemy import create_engine
from sqlalchemy import text

from prompt_template import PROMPT_TEMPLATE, REPHRASE_PROMPT, PROMPT_CORRECTION_TEMPLATE
from utils import get_console_logger
from config import CONNECT_ARGS, MODEL_LIST, ENDPOINT, TEMPERATURE, VERBOSE, DEBUG
from config_private import COMPARTMENT_OCID

logger = get_console_logger()


def create_db_engine():
    """
    Connect to the database and create the DB engine.
    Returns:
        engine (Engine): SQLAlchemy engine instance or None if connection fails.
    """
    try:
        logger.info("Connecting to the Database...")

        # new config, without instant client
        engine = create_engine(
            "oracle+oracledb://:@",
            thick_mode=False,
            connect_args=CONNECT_ARGS,
        )

        logger.info("Connected, DB engine created...")

        return engine
    except Exception as e:
        logger.error("Error setting up SQLDatabase: %s", e)
        return None


def get_chat_models():
    """
    Create a list with all models to be used to generate SQL

    first is used model_list[0],. then if SQL syntax is wrong 1,
    """
    chat_models = [
        ChatOCIGenAI(
            model_id=model,
            service_endpoint=ENDPOINT,
            compartment_id=COMPARTMENT_OCID,
            model_kwargs={"temperature": TEMPERATURE, "max_tokens": 2048},
        )
        for model in MODEL_LIST
    ]

    return chat_models


def format_schema(schema):
    """
    Format the schema information for better readability.
    Args:
        schema (dict): Raw schema information.
    Returns:
        str: Formatted schema string.
    """
    # Split the schema by the CREATE TABLE keyword to separate each table
    tables = schema["table_info"].split("CREATE TABLE")

    # Reconstruct the schema with better formatting
    formatted_schema = []
    for table in tables:
        if table.strip():  # Check if the table is not an empty string
            formatted_schema.append(f"CREATE TABLE {table.strip()}\n{'-'*40}\n")

    if VERBOSE:
        logger.info("Found information for %s tables...", len(tables))
        logger.info("")

    return "\n".join(formatted_schema)


def get_formatted_schema(engine, llm):
    """
    Fetch and format the schema information from the database.
    Args:
        engine (Engine): SQLAlchemy engine instance.
        llm: Language model instance.
    Returns:
        str: Formatted schema string.
    """
    logger.info("Getting schema information...")

    try:
        toolkit = SQLDatabaseToolkit(db=SQLDatabase(engine), llm=llm)
        raw_schema = toolkit.get_context()

        schema = format_schema(raw_schema)

        return schema
    except Exception as e:
        logger.error("Error fetching or formatting schema: %s", e, exc_info=True)
        return ""


def extract_sql_from_response(response_text):
    """
    Extract the SQL query from the LLM-generated response.
    Args:
        response_text (str): Text generated by the LLM.
    Returns:
        str: Extracted SQL query or None if not found.
    """
    if DEBUG:
        logger.info(" Inside extract_sql_from_response")
        logger.info(response_text)

    # sql enclosed in triple backtick
    sql_match = re.search(r"```(.*?)```", response_text, re.DOTALL)

    if sql_match:
        return sql_match.group(1).strip()
    return None


def rephrase_response(original_response, llm):
    """
    Rephrase the response using the language model.
    Args:
        original_response (str): The original response to rephrase.
        llm: Language model instance.
    Returns:
        str: Rephrased response.
    """
    rephrase_prompt = PromptTemplate(
        template=REPHRASE_PROMPT, input_variables=["response"]
    )
    rephrase_chain = rephrase_prompt | llm

    result = rephrase_chain.invoke({"response": original_response})

    return result.content


def _generate_sql(user_query, schema, llm):
    """
    Generate an Oracle SQL query from the user's query and schema information.
    Args:
        user_query (str): User-provided query.
        schema (str): Formatted schema information.
        llm: Language model instance.
    Returns:
        tuple: Generated SQL query and the full response text.
    """
    # Define a custom prompt template that uses the schema information
    # Create the prompt template and LLM chain for generating SQL queries
    prompt = PromptTemplate(
        template=PROMPT_TEMPLATE, input_variables=["schema", "query"]
    )
    llm_chain = prompt | llm

    response = llm_chain.invoke({"schema": schema, "query": user_query})

    sql_query = extract_sql_from_response(response.content)

    return sql_query, response.content


def remove_sql_prefix(input_text):
    """
    Remove 'sql' prefix from the beginning of the SQL query, if present.
    Args:
        input_text (str): The original SQL query.
    Returns:
        str: Cleaned SQL query without the 'sql' prefix.
    """
    stripped_text = input_text.lstrip()

    # Check if the string starts with "sql" and remove it
    if stripped_text.startswith("sql"):
        return stripped_text[4:].lstrip()
    # else
    return stripped_text


def custom_clean(sql_query):
    """
    Post-process the SQL query to make it Oracle-compatible.
    Args:
        sql_query (str): The original SQL query.
    Returns:
        str: Cleaned and processed SQL query.
    """
    # remove ;
    # changed: don't remove \n anymore
    # cleaned_query = sql_query.strip().replace("\n", " ").rstrip(";")
    cleaned_query = sql_query.strip().rstrip(";")

    # remove "sql" for Cohere
    cleaned_query = remove_sql_prefix(cleaned_query)

    return cleaned_query


def generate_sql_query(user_query, schema, llm):
    """
    Combine SQL generation and post-processing.
    Args:
        user_query (str): User-provided query.
        schema (str): Formatted schema information.
        llm: Language model instance.
    Returns:
        tuple: Cleaned SQL query and the full response text.
    """
    # Run the LLM to generate the SQL query
    sql_query, response = _generate_sql(user_query, schema, llm)

    cleaned_query = ""

    if len(sql_query):
        cleaned_query = custom_clean(sql_query)

        if DEBUG:
            logger.info("------------------------")
            logger.info("Generated query:")
            logger.info(sql_query)
            logger.info("")
            logger.info("Cleaned:")
            logger.info(cleaned_query)
    else:
        logger.info("------------------------")
        logger.error("Generated query is empty!!!")

    return cleaned_query, response


def test_sql_query_sintax(sql_text, engine):
    """
    Test the SQL against the DB

    Doesn't fetch records
    """
    with engine.connect() as connection:
        try:
            _ = connection.execute(text(sql_text))

            return True

        except Exception as e:
            logger.error("SQL query sintax errors %s", e)

            return False


def generate_sql_query_with_models(user_query, schema, engine, llm_list):
    """
    Combine SQL generation and post-processing.
    Use a list of models... if with the first get error then try with second
    and so on until one succeed
    Args:
        user_query (str): User-provided query.
        schema (str): Formatted schema information.
        engine: used to test the sintax of the generated query
        llm_list: Language model list
    Returns:
        str: Cleaned SQL query, empty if wrong
    """
    for i, llm in enumerate(llm_list):
        # try model
        cleaned_query, _ = generate_sql_query(user_query, schema, llm)

        if i > 0 and VERBOSE:
            logger.info("Trying with another model...")
            logger.info("")

        # test query
        is_ok = test_sql_query_sintax(cleaned_query, engine)

        if is_ok:
            # break the for
            return cleaned_query

    # here all the models have failed
    logger.error("generate_sql_query_with_models: error with all models.")
    logger.error("")
    logger.error("User query: %s", user_query)

    return ""


def correct_sql_query(user_query, schema, sql_and_error, llm):
    """
    Correct a SQL query with errors.
    This function can be used as a second try if first gives error.

    To be tested
    """
    prompt = PromptTemplate(
        template=PROMPT_CORRECTION_TEMPLATE,
        input_variables=["schema", "query", "sql_and_error"],
    )
    llm_chain = prompt | llm

    try:
        response = llm_chain.invoke(
            {"schema": schema, "query": user_query, "sql_and_error": sql_and_error}
        )
        corrected_sql_query = extract_sql_from_response(response.content)

        cleaned_query = custom_clean(corrected_sql_query)
    except Exception as e:
        logger.error("Error in correct_sql: %s", e)
        cleaned_query = ""

    return cleaned_query, response.content
