"""
REST API for SQL query generation

V2: added management of conversation and routing
"""

import json
from typing import Dict, List
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
from langchain_core.prompts import PromptTemplate

from ai_sql_agent import AISQLAgent
from database_manager import DatabaseManager
from llm_manager import LLMManager
from router import Router
from prompt_template import PROMPT_TEMPLATE
from prompt_routing import PROMPT_CHAT_ON_DATA
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
    INDEX_MODEL_FOR_EXPLANATION,
    VERBOSE,
)
from config_private import COMPARTMENT_OCID


# constants
MEDIA_TYPE_JSON = "application/json"

#
# Main
#
app = FastAPI()

# global Object to handle conversation history
# the key is a str: conv_id
# the value is a Dict, containing
# {"status": status, "type": output_type, "content": output, "msg": msg}

# for now we keep a certain number of round trip (req, resp)
# but for explain we use the last msgs (should contain data)
# 10 re/ai resp.
MAX_MSGS = 20

conversations: Dict[str, List] = {}

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

router = Router(llm_manager)

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


class UserInput(BaseModel):
    """
    class for the body of the request

    conv_id: to mantian the conv session
    user_query: the request from the user
    """

    # for now not really used
    conv_id: str
    user_query: str


#
# supporting functions to manage the conversation
# history (add, get)
#
def add_msg(conv_id: str, msg: dict):
    """
    add a data to a conversation.
    If the conversation doesn't exist create it
    data: rows retrieved from SQL
    """
    if conv_id not in conversations:
        # create it
        if VERBOSE:
            logger.info("Creating conversation id: %s", conv_id)

        conversations[conv_id] = []

    # identify the conversation
    conversation = conversations[conv_id]

    conversation.append(msg)

    # to keep only MAX_NUM_MSGS in the conversation
    if len(conversation) > MAX_MSGS:
        if VERBOSE:
            logger.info("Removing old msg from conversation id: %s", conv_id)
        # remove first (older) el from conversation
        conversation.pop(0)


def get_conversation(v_conv_id):
    """
    return a conversation as List[Message]
    """
    if v_conv_id not in conversations:
        conversation = []
    else:
        conversation = conversations[v_conv_id]

    return conversation


def manage_datetime(rows):
    """
    handles datetime serialization
    """
    # (2/10) handle datetime to solve serialization problem
    for row in rows:
        for key, value in row.items():
            if isinstance(value, datetime):
                row[key] = value.isoformat()

    return rows


@app.post("/generate", tags=["V1"])
def generate(request: UserInput):
    """
    The function handles the request to generate a SQL query

    request: a request in NL
    """
    user_query = request.user_query

    logger.info("User query: %s", user_query)

    if not user_query:
        raise HTTPException(status_code=400, detail="Empty user query")

    sql_query = ""
    try:
        if len(user_query) > 0:
            sql_query = ai_sql_agent.generate_sql_query(user_query, user_group_id=None)

    except Exception as e:
        logger.error("Error generating SQL: %s", e)
        raise HTTPException(status_code=500, detail="Error generating SQL query")

    return JSONResponse(content={"generated_sql": sql_query})


@app.post("/generate_and_exec_sql", tags=["V1"])
def generate_and_exec_sql(request: UserInput):
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

    # (2/10) handle datetime to solve serialization problem
    rows_ser = manage_datetime(rows_ser)

    return Response(content=rows_ser, media_type=MEDIA_TYPE_JSON)


# (L.S: 03/10/2024) I have added a v2 version of the API
# supporting routing and chat on your data
#
# supporting functions for V2
#
def analize_data(user_request, data):
    """
    This function analyze the data provided
    based on the user request using an LLM
    """
    # setup model for data analysis
    analyze_prompt = PromptTemplate.from_template(PROMPT_CHAT_ON_DATA)

    # get llm to be used
    llm_c = llm_manager.llm_models[INDEX_MODEL_FOR_EXPLANATION]

    analyze_chain = analyze_prompt | llm_c

    result = analyze_chain.invoke({"data": data, "question": user_request})

    return result.content


def backward_search(conv):
    """
    search for the first data object in conversation
    starting from bottom of the list
    """
    # backward search
    # if conv is empty return None
    for el in reversed(conv):
        if el["type"] == "data":
            return el
    return None  # not found


def handle_explain_ai_response_v2(request):
    """
    handle a request to analyze or explain data or create a report
    needs: data
    """
    # we need to check that data exist in conversation
    conv = get_conversation(request.conv_id)

    # if we don't find data
    no_msg = "Nothing to analyze. Maybe you should request for some data."

    # search in the conversation, starting from the last to the first
    # the first object of type data
    data = backward_search(conv)

    if data is not None:
        # ok, call LLM to analyze data
        result = analize_data(request.user_query, data)
    else:
        result = no_msg

    return result


def handle_generate_and_exec_sql_v2(request):
    """
    handle a request to generate sql and execute it for v2 api
    """
    user_query = request.user_query

    logger.info("User query: %s...", user_query)

    rows = None
    if len(user_query) > 0:
        sql_query = ai_sql_agent.generate_sql_query(user_query, user_group_id=None)

        if len(sql_query) > 0:
            rows = db_manager.execute_sql(sql_query)

    # serialize each row in a dict
    if rows is not None:
        rows_ser = [to_dict(row) for row in rows]

        # handle serialization of datetime columns
        rows_ser = manage_datetime(rows_ser)
    else:
        rows_ser = []

    return rows_ser


#
# This function wraps the dispatching logic
#
def handle_generic_request_v2(request):
    """
    get a generic request and dispatch
    """

    # classify using the router (LLM based)
    classification = router.classify(request.user_query)

    logger.info("")
    logger.info("Request classified as: %s", classification)

    #
    # Here is the dispatching logic
    #

    # prepare the output for normal
    status = "OK"
    # if ok we return content no msg
    msg = ""

    if classification == "generate_sql":
        # sql generates data
        output_type = "data"
        output = handle_generate_and_exec_sql_v2(request)

    elif classification == "analyze_data":
        # generates a report
        output_type = "analysis"
        output = handle_explain_ai_response_v2(request)

    elif classification == "not_defined":
        output_type = "not_defined"
        # msg to be returned to the user
        output = "Request not defined. Please clarify and/or provide more info."
    else:
        # exception... could it happen? Only if router fails
        # should not happen
        status = "KO"
        output_type = "not classified"
        msg = "Dispatching: Request not correctly classified !"
        output = ""
        logger.error(msg)

    # add to the conversation history
    obj_input = {"status": "OK", "type": "request", "content": request.user_query}
    add_msg(request.conv_id, obj_input)
    # result is a dict with the structure you see below
    obj_output = {"status": status, "type": output_type, "content": output, "msg": msg}
    add_msg(request.conv_id, obj_output)

    # prepare as json for the output
    result = json.dumps(obj_output)

    return result


#
# HTTP Operations for V2
#
@app.post("/v2/handle_data_request", tags=["V2"])
def generic_data_request(request: UserInput):
    """
    Could be generate SQL-and-exec or explain or create a report
    """
    result = handle_generic_request_v2(request)

    return Response(content=result, media_type=MEDIA_TYPE_JSON)


# to clean up a conversation
@app.delete("/v2/delete", tags=["V2"])
def delete(conv_id: str):
    """
    delete a conversation
    """
    if VERBOSE:
        logger.info("Called delete, conv_id: %s...", conv_id)

    if conv_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    del conversations[conv_id]

    return Response(content="", media_type=MEDIA_TYPE_JSON)


#
# Main
#
if __name__ == "__main__":
    uvicorn.run(host=API_HOST, port=API_PORT, app=app)
