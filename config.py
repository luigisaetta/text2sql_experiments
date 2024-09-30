"""
public configurations

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

#
# General settings
#
VERBOSE = True
DEBUG = False

# enable use of reranker (LLM) to select table for SQL generation
ENABLE_RERANKING = True
# if True add the AI explanation
ENABLE_AI_EXPLANATION = True

# for REST API
API_HOST = "0.0.0.0"
API_PORT = 8888

#
# LLM settings
#
# Models are used in this order to generate SQL (second if first fails..)
MODEL_LIST = [
    "meta.llama-3.1-70b-instruct",
    "cohere.command-r-plus",
    "meta.llama-3.1-405b-instruct",
]
# now every model has its own endpoint, check carefully
# must be aligned to MODEL_LIST (405B in Chicago)
MODEL_ENDPOINTS = [
    "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com",
    "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com",
    "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",
]
# index, in above lists of model for summary, reranking, explanation
# (index start by 0)
INDEX_MODEL_FOR_SUMMARY = 2
INDEX_MODEL_FOR_RERANKING = 2
INDEX_MODEL_FOR_EXPLANATION = 2

TEMPERATURE = 0
MAX_TOKENS = 4000

# the way we handle auth for GenAI
AUTH_TYPE = "API_KEY"

# for embeddings
EMBED_MODEL_NAME = "cohere.embed-english-v3.0"
EMBED_ENDPOINT = "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com"

#
# DB connectivity settings
#
# here we consolidate in a single structure configs to access DB
# data DB config: this is to connect the data schema
WALLET_DIR = "/Users/lsaetta/Progetti/text2sql_experiments/WALLET"
# ebiz uk sandbox
# WALLET_DIR = "/Users/lsaetta/Progetti/text2sql_experiments/WALLET_EBIZ"

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

# this one is dedicated to Ebiz tests
# VECTOR_TABLE_NAME = "SCHEMA_VECTORS"
# this one is dedicated to our internal tests
VECTOR_TABLE_NAME = "SCHEMA_VECTORS_SH"

# the strategy for similarity search Don't change
DISTANCE_STRATEGY = DistanceStrategy.COSINE

# the table where we store a list of user_queries for each table in the data schema
TABLE_NAME_SQ = "sample_queries"

# Data Schema
# this config is to limit the list of tables we read from the Data Schema
# should contain a prefix like D_ or ALL
INCLUDE_TABLES_PREFIX = "ALL"


# number of samples read from each table
N_SAMPLES = 3


#
# Similarity search and reranking
#
# parameters for schema partitioning
# number of tables identified to satisfy the query
# with similarity search
# for now we support only join max 6 tables...
TOP_K = 6
# top_n after reranking
TOP_N = 6
