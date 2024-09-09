"""
public configurations

changed: 9/9/2024, pnly private config (pwd) left in config_private
"""

from config_private import DB_USER, DB_PWD, DSN, WALLET_PWD

VERBOSE = True
DEBUG = False

ENDPOINT = "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com"

# 2/09 inverted the list, first Llama3
MODEL_LIST = ["meta.llama-3-70b-instruct", "cohere.command-r-plus"]
TEMPERATURE = 0

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
ENABLE_AI_EXPLANATION = False
