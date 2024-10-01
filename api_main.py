"""
REST API for SQL query generation
"""

import json

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel

from ai_sql_agent import AISQLAgent
from database_manager import DatabaseManager
from llm_manager import LLMManager

from prompt_template import PROMPT_TEMPLATE
from utils import get_console_logger, to_dict
from config import (
    CONNECT_ARGS,
    MODEL_LIST,
    MODEL_ENDPOINTS,
    EMBED_MODEL_NAME,
    EMBED_ENDPOINT,
    TEMPERATURE,
    API_HOST,
    API_PORT,
)
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


# Initialize the agent, only once !!!
ai_sql_agent = AISQLAgent(
    CONNECT_ARGS,
    MODEL_LIST,
    MODEL_ENDPOINTS,
    COMPARTMENT_OCID,
    EMBED_MODEL_NAME,
    EMBED_ENDPOINT,
    TEMPERATURE,
    PROMPT_TEMPLATE,
)


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

    if not user_query:
        raise HTTPException(status_code=400, detail="Empty user query")

    try:
        if len(user_query) > 0:
            sql_query = ai_sql_agent.generate_sql_query(user_query, user_group_id=None)

    except Exception as e:
        logger.error("Error generating SQL: %s", e)
        raise HTTPException(status_code=500, detail="Error generating SQL query")

    return JSONResponse(content={"generated_sql": sql_query})


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
        sql_query = ai_sql_agent.generate_sql_query(user_query, user_group_id=None)

        if len(sql_query) > 0:
            rows = db_manager.execute_sql(sql_query)

    # serialize each row in a dict
    rows_ser = [to_dict(row) for row in rows]

    json_data = json.dumps(rows_ser)

    return Response(content=json_data, media_type=MEDIA_TYPE_JSON)


@app.post("/explain_ai_response/", tags=["V1"])
def explain_ai_response(request: AIAnswerInput):
    """
    To explain the dataset retrieved with AI
    """
    logger.info("Explain: %s", request)

    raise NotImplementedError("Explain not yet implemented.")


if __name__ == "__main__":
    uvicorn.run(host=API_HOST, port=API_PORT, app=app)
