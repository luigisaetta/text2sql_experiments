"""
public configurations

changed: 9/9/2024, only private config (pwd) left in config_private
"""

from langchain_community.vectorstores.utils import DistanceStrategy

# embed private config
from config_private import (
    # data schema
    DB_USER,
    DB_PWD,
    DSN,
    WALLET_PWD,
    # vector schema
    VECTOR_DB_USER,
    VECTOR_DB_PWD,
    VECTOR_DSN,
    VECTOR_WALLET_PWD,
)

VERBOSE = True
DEBUG = False

# LLM config
ENDPOINT = "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com"

# 2/09 inverted the list, first Llama3. Don't change the order
MODEL_LIST = ["meta.llama-3-70b-instruct", "cohere.command-r-plus"]
TEMPERATURE = 0
MAX_TOKENS = 1024

# the way we handle auth for GenAI
AUTH_TYPE = "API_KEY"

# for embeddings
EMBED_MODEL_NAME = "cohere.embed-english-v3.0"

# here we consolidate in a single structure configs to access DB
# data DB config: this is to connect the data schema
WALLET_DIR = "/Users/lsaetta/Progetti/text2sql_experiments/WALLET"

CONNECT_ARGS = {
    "user": DB_USER,
    "password": DB_PWD,
    "dsn": DSN,
    "config_dir": WALLET_DIR,
    "wallet_location": WALLET_DIR,
    "wallet_password": WALLET_PWD,
}

# for VECTOR DB config: this is to connect to the vector store schema
# could be the same or a nother wallet, depends on DB used.
# DB_USER is different !!! Don't put the VECTORS in the data schema
VECTOR_WALLET_DIR = "/Users/lsaetta/Progetti/text2sql_experiments/WALLET_VECTOR"

CONNECT_ARGS_VECTOR = {
    "user": VECTOR_DB_USER,
    "password": VECTOR_DB_PWD,
    "dsn": VECTOR_DSN,
    "config_dir": VECTOR_WALLET_DIR,
    "wallet_location": VECTOR_WALLET_DIR,
    "wallet_password": VECTOR_WALLET_PWD,
}
# the name of the table where we store tables summary and embeddings
VECTOR_TABLE_NAME = "SCHEMA_VECTORS"
# the strategy for similarity search Don't change
DISTANCE_STRATEGY = DistanceStrategy.COSINE

# if True add the AI explanation
ENABLE_AI_EXPLANATION = True

# parameters for schema partitioning
# number of tables identified to satisfy the query
# with similarity search
# for now we support only join max 6 tables...
TOP_N = 6

# for REST API
PORT = 8888
