"""
REST API for SQL query generation
"""

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
)
from utils import get_console_logger
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


class GenerateSQLInput(BaseModel):
    """
    class for the body of the request

    user_query: the request from the user
    """

    user_query: str


@app.post("/generate/", tags=["V1"])
def generate(request: GenerateSQLInput):
    user_query = request.user_query

    logger.info("User query: %s", user_query)

    if len(user_query) > 0:
        sql_query = generate_sql_query_with_models(
            user_query, schema, engine, model_list
        )

        if len(sql_query) > 0:
            return Response(content=sql_query, media_type=MEDIA_TYPE_TEXT)
        else:
            return Response(content="", media_type=MEDIA_TYPE_TEXT)


if __name__ == "__main__":
    # to be faster schema is global
    model_list = get_chat_models()
    llm1 = model_list[0]

    engine = create_db_engine()

    schema = get_formatted_schema(engine, llm1)

    uvicorn.run(host="0.0.0.0", port=PORT, app=app)
