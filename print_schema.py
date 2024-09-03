"""
Print the current schema
"""

from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI

from core_functions import create_db_engine, get_formatted_schema
from config_private import MODEL_LIST, ENDPOINT, COMPARTMENT_OCID

llm = ChatOCIGenAI(
    # test using Llama3
    model_id=MODEL_LIST[0],
    service_endpoint=ENDPOINT,
    compartment_id=COMPARTMENT_OCID,
    model_kwargs={"temperature": 0, "max_tokens": 2048},
)

engine = create_db_engine()

SCHEMA = get_formatted_schema(engine, llm)

print(SCHEMA)
