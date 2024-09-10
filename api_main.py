"""
REST API for SQL query generation
"""

import json

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel


from core_functions import (
    get_chat_models,
    generate_sql_query_with_models,
    create_db_engine,
    get_formatted_schema,
    execute_sql,
    explain_response,
)
from utils import get_console_logger, to_dict
from config import PORT

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

model_list = get_chat_models()
llm1 = model_list[0]
llm2 = model_list[1]

engine = create_db_engine()
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
        sql_query = generate_sql_query_with_models(
            user_query, SCHEMA, engine, model_list
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
        sql_query = generate_sql_query_with_models(
            user_query, SCHEMA, engine, model_list
        )
        if len(sql_query) > 0:
            rows = execute_sql(sql_query, engine)

    rows_ser = [to_dict(row) for row in rows]

    json_data = json.dumps(rows_ser)

    return Response(content=json_data, media_type=MEDIA_TYPE_JSON)


@app.post("/explain_ai_response/", tags=["V1"])
def explain_ai_response(request: AIAnswerInput):
    user_request = request.user_query
    rows = request.rows

    # using r-plus for interpretation
    ai_response = explain_response(user_request, rows, llm2)

    json_data = json.dumps(ai_response)

    return Response(content=json_data, media_type=MEDIA_TYPE_JSON)


if __name__ == "__main__":
    # to be faster schema is global
    uvicorn.run(host="0.0.0.0", port=PORT, app=app)
