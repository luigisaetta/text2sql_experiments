"""
REST API for SQL query generation

V2: added management of conversation and routing
V 2.1: added complete chat with data
"""

import json
from typing import Dict, List
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel

from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

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

# key is the conv_id, value is a list of msgs
conversations: Dict[str, List[BaseMessage]] = {}

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

# this are preamble and template used for chat with your data
PREAMBLE = """You are an AI assistant.
Your task is to explain the provided data and respond to requests 
by referencing both the given data and the conversation history.
Base your answers strictly on the provided information and prior messages in the conversation.
"""

analyze_template = ChatPromptTemplate.from_messages(
    [("system", PREAMBLE), MessagesPlaceholder("msgs")]
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
def add_msg(conv_id: str, msg: BaseMessage):
    """
    add msg to a conversation.
    If the conversation doesn't exist create it

    msg can be:
    - a message with data
    - a message with human request
    -the answer from a model
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
def explain_ai_response_v2(request) -> AIMessage:
    """
    handle a request to analyze or explain data or create a report

    This function analyze the data
    based on the user request using an LLM

    data should be already in the chat history
    the user request is the last msg in history
    """
    # add the last request
    new_msg = HumanMessage(request.user_query)
    add_msg(request.conv_id, new_msg)

    msgs = get_conversation(request.conv_id)

    # build the chain
    llm_c = llm_manager.llm_models[INDEX_MODEL_FOR_EXPLANATION]

    analyze_chain = analyze_template | llm_c

    ai_message = analyze_chain.invoke({"msgs": msgs})

    return ai_message


def generate_and_exec_sql_v2(request):
    """
    handle a request to generate sql and execute it for v2 api

    for now it doesn't use msg history
    """
    user_query = request.user_query

    logger.info("User query: %s...", user_query)

    # add the last request
    new_msg = HumanMessage(user_query)
    add_msg(request.conv_id, new_msg)

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
        else:
            # SQL not generated
            logger.info("User query: %s", user_query)
            logger.error("SQL Agent: Not able to generate SQL.")
            raise ValueError("SQL Agent: Not able to generate SQL.")
    else:
        # not received request
        logger.error("No user request.")
        raise ValueError("User request not provided.")

    return rows_ser


#
# This function wraps the dispatching logic
#
def handle_generic_request_v2(request):
    """
    get a generic request and dispatch
    """

    logger.info("")
    logger.info("Request received: %s", request.user_query)

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

        try:
            # try to catch the case where the SQL generated is not correct
            output = generate_and_exec_sql_v2(request)

        except ValueError:
            # return an error to UI
            msg = "SQL not generated !"
            obj_output = {
                "status": "KO",
                "type": output_type,
                "content": "",
                "msg": msg,
            }
            result = json.dumps(obj_output)

            return result

    elif classification == "analyze_data":
        # generates a report
        ai_message = explain_ai_response_v2(request)

        output_type = "analysis"
        output = ai_message.content

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

    # add the input to the conversation history is handled by the function handling the request

    if classification == "generate_sql":
        # add output data to msgs history
        data_msg = HumanMessage(
            content="These are the data for your analysis.\nData:\n" + str(output)
        )

        add_msg(request.conv_id, data_msg)
    else:
        # add the answer from LLM
        add_msg(request.conv_id, AIMessage(output))

    obj_output = {"status": status, "type": output_type, "content": output, "msg": msg}
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


# to get the stats
@app.get("/v2/get_cache_stats", tags=["V2"])
def get_cache_stats():
    """
    read the stats from the cache
    """
    all_stats = ai_sql_agent.request_cache.get_all_stats()

    # uniform output
    obj_output = {"status": "OK", "type": "data", "content": all_stats, "msg": ""}

    return JSONResponse(content=obj_output, status_code=200)


#
# Main
#
if __name__ == "__main__":
    uvicorn.run(host=API_HOST, port=API_PORT, app=app)
