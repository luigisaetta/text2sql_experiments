"""
public configurations

changed: 9/9/2024, pnly private config (pwd) left in config_private
"""

from config_private import DB_USER, DB_PWD, DSN, WALLET_PWD

VERBOSE = True
DEBUG = False

# LLM config
ENDPOINT = "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com"

# 2/09 inverted the list, first Llama3
MODEL_LIST = ["meta.llama-3-70b-instruct", "cohere.command-r-plus"]
TEMPERATURE = 0

# the way we handle auth for GenAI
AUTH_TYPE = "API_KEY"

# for embeddings
EMBED_MODEL_NAME = "cohere.embed-english-v3.0"

# DB config
WALLET_DIR = "/Users/lsaetta/Progetti/text2sql_experiments/WALLET"

CONNECT_ARGS = {
    "user": DB_USER,
    "password": DB_PWD,
    "dsn": DSN,
    "config_dir": WALLET_DIR,
    "wallet_location": WALLET_DIR,
    "wallet_password": WALLET_PWD,
}

# if True add the AI explanation
ENABLE_AI_EXPLANATION = True

# parameters for schema partitioning
# number of tables identified to satisfy the query
# with similarity search
TOP_N = 6

# for REST API
PORT = 8888
