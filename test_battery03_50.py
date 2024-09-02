"""
Battery of test02

These are tests generated by GPT-=
"""

from tqdm import tqdm
from sqlalchemy import text
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI

from core_functions import create_db_engine, get_formatted_schema, generate_sql_query

from config_private import ENDPOINT, COMPARTMENT_OCID, MODEL_LIST

# SH schema
USER_QUERIES = [
    "Retrieve the product names and the total amount sold for each product.",
    "List the product names, product categories, and sales channels used by customers from Italy.",
    """Find the customer names, products purchased, and promotions used by customers in the 'Catalog' channel.""",
    """Get the list of sales, including product names, customer names, and customer regions for purchases made in 1998.""",
    """List the promotion names, customer names, and cities of customers who used these promotions. Limit only to first 50 rows""",
    "Find the product names, subcategories, and promotion names used for products sold in Asia.",
    """Get the list of customers, products purchased, and sales channels for sales that took place during the summer of 1998.""",
    """Find the customer names and their cities who purchased products through the 'Tele Sales' channel and used promotions with a cost greater than 1000.""",
    """Find the promotion names, promotion categories, and cities of customers who participated in these promotions. Limit only to first 50 rows""",
    """Get the list of customers, product names, sales channel names, and promotion names used for each sale in 1998. Limit only to first 50 rows""",
    "List the customer names, their income levels, and products purchased by customers from Japan.",
    """Find the product category names, customer regions, and sales channel names for sales made through the 'Direct Sales' channel.""",
    """Get the list of promotions, product names, customer regions, and sales channel names used for each sale. Get only first 30 rows""",
    """Find the product names, subcategories, customer names, and cities of customers 
    who purchased these products. Get only first 30 rows""",
    """List the product category names, customer names, and promotion names used 
    for each sale made in Europe.""",
    """Find the customer names, cities, and promotion names for sales 
    that occurred in the 'Indirect' channel.""",
    """Get the list of sales, including product names, categories, 
    and customer regions for sales with an amount greater than 1000.""",
    "Find the product names and promotions used for those products sold in the 'Catalog' channel.",
    """List the customer names, product names, and subcategories 
    for sales made through promotions with a cost less than 500. Get only firt 60 rows""",
    """Find the customer names, cities, product categories, 
    and promotion names for sales that occurred in 1999.""",
    """Get the list of customers, their income levels, product names purchased, 
    and sales channels used.""",
    "Find the promotion names, sales channel names, and product names sold in Asia through these promotions.",
    "List the customer names, their cities, and product category names purchased through the 'Tele Sales' channel.",
    "Find the product names and cities of customers who purchased these products through promotions active before 1998.",
    "Get the list of product names, their categories, customer names, and sales channels used.",
    "Find the promotion names, subcategories, customer cities, and sales channels used for each sale.",
    "List the product names, categories, customer regions, and promotion names for sales made in North America.",
    "Find the customer names, their incomes, cities, and product names purchased through the 'Direct Sales' channel.",
    "Get the list of promotion names, customer names, cities, and regions for each sale made in Europe.",
    "Find the product names, their subcategories, promotion names for sales that occurred in the 'Catalog' channel.",
    "List the customer names, cities, regions, and product names purchased through promotions active before 1999.",
    "Find the customer names, product names, and product categories purchased through the 'Indirect' channel.",
    "Get the list of promotion names, product names, customer cities, and sales channels used.",
    "Find the customer names, their incomes, product names, and cities for sales that occurred in 1999.",
    "List the product names, categories, customer names, and promotion names used for sales made in Europe.",
    "Find the promotion names, categories, customer names, and regions for each sale made through the 'Direct Sales' channel.",
    "Get the list of product names, their categories, customer names, and cities for sales with an amount greater than 1500.",
    "Find the customer names, promotion names, cities, and regions for sales that occurred in the 'Tele Sales' channel.",
    "List the product names, categories and promotion names used for each sale.",
    "Find the customer names, their incomes, cities, and promotion names used for each sale made in Asia.",
    "Get the list of product names, categories, sales channel names, and promotion names used.",
    "Find the promotion names, categories, customer names, and product names sold through the 'Catalog' channel.",
    "List the customer names, their cities, product names, and sales channels used for sales made before 1999.",
    "Find the customer names, promotion names, cities, and product names for sales that occurred in the 'Indirect' channel.",
    "Get the list of product names, categories, customer cities, and promotion names used.",
    "Find the customer names, their incomes, regions, and promotion names used for each sale made in North America.",
    "List the product names, categories, regions, and promotion names used for sales made through the 'Direct Sales' channel.",
    "Find the customer names, their cities, product names, and promotion names used for sales made in 1998.",
    "Get the list of promotion names, categories, customer names, and cities for each sale made in Asia.",
    """Find the product names, their categories, promotion names, 
    and customer names for sales that occurred through the 'Catalog' channel.""",
]

# 0 is command-r-plus
MODEL_NAME = MODEL_LIST[0]

llm = ChatOCIGenAI(
    model_id=MODEL_NAME,
    service_endpoint=ENDPOINT,
    compartment_id=COMPARTMENT_OCID,
    model_kwargs={"temperature": 0, "max_tokens": 2048},
)

engine = create_db_engine()

SCHEMA = get_formatted_schema(engine, llm)

N_QUERIES = 0
N_OK = 0

print("")
print("LLM used is: ", MODEL_NAME)
print("")

for user_query in tqdm(USER_QUERIES):
    N_QUERIES += 1
    sql_query, response = generate_sql_query(user_query, SCHEMA, llm)

    # check if SQL sintax is correct
    with engine.connect() as connection:
        try:
            result = connection.execute(text(sql_query))
            # don't need fetchall to check sintax
            # rows = result.fetchall()

            N_OK += 1
        except Exception as e:
            print("---------------------")
            print(f"Query n. {N_QUERIES}:")
            print(user_query)
            print("")
            print(e)
            print("---------------------")

print("")
print("Summary of Test results:")
print("Number of queries: ", N_QUERIES)
print("Number of test ok: ", N_OK)
