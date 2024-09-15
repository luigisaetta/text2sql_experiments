"""
To compare SQL generated with Golden query (generated by another LLM)
"""

import re
import warnings
import logging
import heapq

import bert_score

from tqdm import tqdm

from database_manager import DatabaseManager
from llm_manager import LLMManager

from core_functions import generate_sql_with_models, get_formatted_schema
from prompt_template import PROMPT_TEMPLATE
from utils import get_console_logger
from config import CONNECT_ARGS, MODEL_LIST, ENDPOINT, TEMPERATURE
from config_private import COMPARTMENT_OCID


def normalize_sql(input_sql):
    """
    apply some normalizations to SQL to make comparison and compute of bert score easier
    """
    # normalize the generated sql
    # remove newline -> single line
    query_generated = input_sql.replace("\n", " ")
    # replace multiple blanks adiacent with a single blank
    query_generated = re.sub(r"\s+", " ", query_generated)

    return query_generated


def find_indexes_of_lowest_values(values, n=5):
    """
    to get the list of bottom 5 pairs with lowest F1
    """
    # Use enumerate to pair values with their indexes
    indexed_values = list(enumerate(values))

    # Find the n smallest values along with their indexes using heapq.nsmallest
    lowest_values_with_indexes = heapq.nsmallest(n, indexed_values, key=lambda x: x[1])

    # Extract the indexes of the n smallest values
    lowest_indexes = [index for index, value in lowest_values_with_indexes]

    return lowest_indexes


#
# Main
#
# suppress warnings for bert score
warnings.filterwarnings(
    "ignore", category=FutureWarning, module="transformers.tokenization_utils_base"
)
logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)


# SH schema
# file with NL requests
TESTS_FILE_NAME = "testsh30_ita.txt"
GOLDEN_TRUTH_FILE = "golden_truth_sh50.txt"

# TESTS_FILE_NAME = "testhr30.txt"
# GOLDEN_TRUTH_FILE = "golden_truth_hr30.txt"
# file with expected (golden) SQL


# read list of NL requests
with open(TESTS_FILE_NAME, "r", encoding="UTF-8") as file:
    USER_QUERIES = [linea.strip() for linea in file]

# read golden truth
sql_queries = []
with open(GOLDEN_TRUTH_FILE, "r", encoding="UTF-8") as g_file:
    for linea in g_file:
        if linea.startswith("#"):
            # comment, ignore
            pass
        else:
            # remove " at beginning and end
            linea = linea.replace('"', "")
            sql_queries.append(linea)

logger = get_console_logger()

db_manager = DatabaseManager(CONNECT_ARGS, logger)
llm_manager = LLMManager(MODEL_LIST, ENDPOINT, COMPARTMENT_OCID, TEMPERATURE, logger)

SCHEMA = get_formatted_schema(
    db_manager.engine,
    # 0 is Llama3
    llm_manager.get_llm_models()[0],
)

# to limit how many we test
TO_TEST = 30

# put the generated sql in this list
generated_sql_list = []

# these are the expected sql
sql_queries = sql_queries[:TO_TEST]
USER_QUERIES = USER_QUERIES[:TO_TEST]


print("")
print("Generating SQL...")
print("")

total_length = min(len(USER_QUERIES), len(sql_queries))

for user_query, sql_query in tqdm(zip(USER_QUERIES, sql_queries), total=total_length):

    sql_query = generate_sql_with_models(
        user_query, SCHEMA, db_manager, llm_manager, PROMPT_TEMPLATE
    )

    # normalize the generated sql
    # remove newline -> single line
    sql_query_normalized = normalize_sql(sql_query)

    generated_sql_list.append(sql_query_normalized)

generated_sql_list = generated_sql_list[:TO_TEST]

# Calculate BERTScore
print("")
print("Computing BERT score...")
print("")
P, R, F1 = bert_score.score(generated_sql_list, sql_queries, lang="en", verbose=True)

print("")
print("Scores:")
print("")

for i, (p, r, f) in enumerate(zip(P, R, F1)):
    print(f"SQL Pair {i+1}: Precision: {p:.4f}, Recall: {r:.4f}, F1 Score: {f:.4f}")

print("")
print("Analyze lower F1 scores...")
print("")
lowest_5_indexes = find_indexes_of_lowest_values(F1, n=5)

# in order of increasing F1
for ind in lowest_5_indexes:
    print("User request: ", USER_QUERIES[ind])
    print("Generated: ", generated_sql_list[ind])
    print("Expected: ", sql_queries[ind])
    print(f"F1 score: {F1[ind]:.4f}")
    print("\n\n")
