"""
Test BM25
"""

import json
import oracledb
from rank_bm25 import BM25Okapi

from database_manager import DatabaseManager
from llm_manager import LLMManager
from schema_manager_23ai import SchemaManager23AI
from langchain_community.embeddings import OCIGenAIEmbeddings

from config import (
    CONNECT_ARGS_VECTOR,
    CONNECT_ARGS,
    VECTOR_TABLE_NAME,
    AUTH_TYPE,
    EMBED_MODEL_NAME,
    EMBED_ENDPOINT,
    MODEL_LIST,
    MODEL_ENDPOINTS,
    TEMPERATURE,
    TOP_N,
)
from config_private import COMPARTMENT_OCID
from utils import get_console_logger


class BM25Retriever:
    """ """

    def __init__(self, logger):
        self.logger = logger
        self.registry = {}

    def _get_tables_chunks(self):
        query_table_chunks = f"""SELECT TEXT, METADATA FROM {VECTOR_TABLE_NAME}"""

        with oracledb.connect(**CONNECT_ARGS_VECTOR) as conn:
            cursor = conn.cursor()

            cursor.execute(query_table_chunks)

            self.logger.info("Reading schema...")
            corpus = []
            for text, metadata in cursor:
                clob_text = text.read()
                clob_metadata = metadata.read()
                # to extract fields of metadata
                json_metadata = json.loads(clob_metadata)

                table_name = json_metadata["table"]
                table_chunk = json_metadata["table_chunk"]

                aggr_table_chunk = clob_text + "\n\n" + table_chunk

                self.logger.info(table_name)
                # self.logger.info("len clob_text: %s", len(clob_text))

                self.registry[table_name] = aggr_table_chunk

                # create the corpus
                corpus.append(aggr_table_chunk)

            self.corpus = corpus

    def index(self):
        # populate the corpus
        retriever._get_tables_chunks()

        tokenized_corpus = [doc.split(" ") for doc in self.corpus]

        self.bm25 = BM25Okapi(tokenized_corpus)

    def search(self, user_query, top_n):
        tokenized_query = user_query.split(" ")

        results = self.bm25.get_top_n(tokenized_query, self.corpus, n=top_n)

        return results


#
# Main
#
logger = get_console_logger()

# now battery of test using SH schema:
TESTS_FILE_NAME = "testsh50.txt"
# TESTS_FILE_NAME = "testhr30.txt"
# TESTS_FILE_NAME = "testhr_problems.txt"
# TESTS_FILE_NAME = "testsh30_ita.txt"
# TESTS_FILE_NAME = "test_hospital.txt"


# read the file with users requests
with open(TESTS_FILE_NAME, "r", encoding="UTF-8") as file:
    USER_QUERIES = [linea.strip() for linea in file]

# read the file with the list of table expected for each request
TABLES_SH50_GOLD_FILE = "tables_sh50_all.txt"

with open(TABLES_SH50_GOLD_FILE, "r", encoding="UTF-8") as file:
    # table name is made upper case
    # I need to remove in some elements an initial blank
    tables_gold_list = [
        [elemento.strip() for elemento in linea.upper().strip().split(",")]
        for linea in file
    ]

db_manager = DatabaseManager(CONNECT_ARGS, logger)
llm_manager = LLMManager(
    MODEL_LIST, MODEL_ENDPOINTS, COMPARTMENT_OCID, TEMPERATURE, logger
)

embed_model = OCIGenAIEmbeddings(
    auth_type=AUTH_TYPE,
    model_id=EMBED_MODEL_NAME,
    service_endpoint=EMBED_ENDPOINT,
    compartment_id=COMPARTMENT_OCID,
)

logger.info("")
logger.info("Loading Schema Manager...")

schema_manager = SchemaManager23AI(db_manager, llm_manager, embed_model, logger)

retriever = BM25Retriever(logger)

logger.info("")
logger.info("Indexing...")
retriever.index()

bm25_hits = 0
vectors_hits = 0
reranked_hits = 0
combined_hits = 0

# to verify the reduction of tahles with reranker
tot_without_reranker = 0
tot_with_reranker = 0

for user_query, expected_tables in zip(USER_QUERIES, tables_gold_list):

    logger.info("User query: %s", user_query)

    results = retriever.search(user_query, TOP_N)

    # the name of the table is in the first line of the chunk
    found_with_bm25 = [chunk.split("\n")[0] for chunk in results]

    # comparison with Vector Search
    with oracledb.connect(**CONNECT_ARGS_VECTOR) as conn:
        results = schema_manager._similarity_search(user_query, conn)

        found_with_vectors = [doc.metadata["table"] for doc in results]

        restricted_schema_parts = []

        # prepare data for reranking
        for doc in results:
            table_name = doc.metadata.get("table")

            # retrieve the portion of schema for the table
            table_chunk = doc.metadata.get("table_chunk")

            if table_chunk:
                restricted_schema_parts.append(table_chunk)
            else:
                logger.warning("No chunk found for table %s", table_name)

        # Join the accumulated chunks into a single string
        restricted_schema = "".join(restricted_schema_parts)

    logger.info("Reranking...")
    found_reranked = schema_manager._rerank_table_list(user_query, restricted_schema)

    # combined_search: union
    found_combined = list(set(found_with_bm25) | set(found_with_vectors))

    # do counts
    for tab in found_with_bm25:
        if tab in expected_tables:
            bm25_hits += 1
    for tab in found_with_vectors:
        if tab in expected_tables:
            vectors_hits += 1
    for tab in found_reranked:
        if tab in expected_tables:
            reranked_hits += 1
    for tab in found_combined:
        if tab in expected_tables:
            combined_hits += 1

    tot_without_reranker += len(found_with_vectors)
    tot_with_reranker += len(found_reranked)

# Final results
tot_tables = sum(len(sottolista) for sottolista in tables_gold_list)

logger.info("")
logger.info("")
logger.info("Search metrics:")
logger.info("Hit Ratio BM25: %3.2f", (bm25_hits / tot_tables))
logger.info("Hit Ratio Vector: %3.2f", (vectors_hits / tot_tables))
logger.info("Hit Ratio Fusion: %3.2f", (combined_hits / tot_tables))
logger.info("Hit Ratio Reranked: %3.2f", (reranked_hits / tot_tables))
logger.info(
    "Avg. num. of tables with vs: %2.0f",
    (float(tot_without_reranker) / len(USER_QUERIES)),
)
logger.info(
    "Avg. num. of tables with reranker: %2.0f",
    (float(tot_with_reranker) / len(USER_QUERIES)),
)
logger.info("")
