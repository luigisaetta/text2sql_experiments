"""
REST API for SQL query generation
"""

import json

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel


from database_manager import DatabaseManager
from llm_manager import LLMManager

from core_functions import (
    get_formatted_schema,
    generate_sql_with_models,
)
from prompt_template import PROMPT_TEMPLATE
from utils import get_console_logger, to_dict
from config import CONNECT_ARGS, MODEL_LIST, MODEL_ENDPOINTS, TEMPERATURE, PORT
from config_private import COMPARTMENT_OCID


# constants
MEDIA_TYPE_TEXT = "text/plain"
MEDIA_TYPE_JSON = "application/json"

#
# Main
#
app = FastAPI()
logger = get_console_logger()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_manager = DatabaseManager(CONNECT_ARGS, logger)
llm_manager = LLMManager(
    MODEL_LIST, MODEL_ENDPOINTS, COMPARTMENT_OCID, TEMPERATURE, logger
)

engine = db_manager.engine
# 0 is llama3-70B
llm1 = llm_manager.llm_models[0]

SCHEMA = get_formatted_schema(engine, llm1)


class GenerateSQLInput(BaseModel):
    """
    class for the body of the request

    conv_id: to mantian the conv session
    user_query: the request from the user
    """

    # for now not really used
    conv_id: str
    user_query: str


class AIAnswerInput(BaseModel):
    """
    class for the body of the request

    ai_answer:
    """

    # for now not really used
    conv_id: str
    user_query: str
    rows: list


@app.post("/generate/", tags=["V1"])
def generate(request: GenerateSQLInput):
    """
    The function handles the request to generate a SQL query

    request: a request in NL
    """
    user_query = request.user_query

    logger.info("User query: %s", user_query)

    content = ""

    if len(user_query) > 0:
        sql_query = generate_sql_with_models(
            user_query, SCHEMA, db_manager, llm_manager, PROMPT_TEMPLATE
        )

        if len(sql_query) > 0:
            content = sql_query

    json_data = json.dumps(content)

    return Response(content=json_data, media_type=MEDIA_TYPE_JSON)


@app.post("/generate_and_exec_sql/", tags=["V1"])
def generate_and_exec_sql(request: GenerateSQLInput):
    """
    generate SQL and then execute

    return a JSON object with the rows read from DB
    """
    user_query = request.user_query

    logger.info("User query: %s...", user_query)

    rows = None
    if len(user_query) > 0:
        sql_query = generate_sql_with_models(
            user_query, SCHEMA, db_manager, llm_manager, PROMPT_TEMPLATE
        )
        if len(sql_query) > 0:
            rows = db_manager.execute_sql(sql_query)

    rows_ser = [to_dict(row) for row in rows]

    json_data = json.dumps(rows_ser)

    return Response(content=json_data, media_type=MEDIA_TYPE_JSON)


@app.post("/explain_ai_response/", tags=["V1"])
def explain_ai_response(request: AIAnswerInput):
    """
    To explain the dataset retrieved with AI
    """
    json_data = "To be implemented..."

    return Response(content=json_data, media_type=MEDIA_TYPE_JSON)


if __name__ == "__main__":
    # to be faster schema is global
    uvicorn.run(host="0.0.0.0", port=PORT, app=app)
