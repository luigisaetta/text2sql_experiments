"""
Prompts and examples
"""

# improved (9/9/2024)
REPHRASE_PROMPT = """
User has made an initial request, reported below.
A SQL query has been executed to retrieve relevant data.
Explain the provided data in a clear and human understandable format.
Be assertive.
Format response in markdown.

## plotting instructions
If the request asks for plotting the data generate the correct Python code
to plot the data using matplotlib library.
Align labels at 90 degrees.
 
 User request:
 {user_request}
 Data retrieved from database:
 {data}"""

# the list of few shot examples is here
EXAMPLES = """"
User query: give me examples of questions I can ask about our data
SQL Query: SELECT t.table_name, c.column_name FROM user_tables t JOIN user_tab_columns c
ON t.table_name = c.table_name ORDER BY t.table_name, c.column_id

User Query: list top 10 sales give customer name and product name
SQL Query: SELECT c.cust_first_name || ' ' || c.cust_last_name AS customer_name, p.prod_name AS product_name, s.quantity_sold, s.amount_sold 
FROM sales s JOIN customers c ON s.cust_id = c.cust_id JOIN products p ON s.prod_id = p.prod_id ORDER BY s.amount_sold 
DESC FETCH FIRST 10 ROWS ONLY

User Query: Describe table SALES
SQL Query: SELECT column_name, data_type FROM user_tab_columns WHERE table_name = 'SALES'

User Query: describe the sales table, list all available columns
SQL Query: SELECT column_name, data_type FROM user_tab_columns WHERE table_name = 'SALES'

User query: Describe table CUSTOMERS
SQL Query: SELECT column_name, data_type FROM user_tab_columns WHERE table_name = 'CUSTOMERS'

User Query: How many suppliers are there?
SQL Query: SELECT COUNT(*) FROM suppliers

User Query: How many supplier are TAX AUTHORITY?
SQL Query: SELECT COUNT(*) FROM Suppliers WHERE supplier_type_code = 'TAX AUTHORITY'

User Query: What is the total amount for invoices with a payment currency of USD from 'company1'?
SQL Query: SELECT SUM(invoice_amount) AS total_amount FROM ap_invoices WHERE payment_currency = 'USD' AND UPPER(supplier_name) LIKE '%COMPANY1%'

User Query: list top 5 invoices with highest amount
SQL Query:  SELECT * FROM ap_invoices ORDER BY invoice_amount DESC FETCH FIRST 5 ROWS ONLY

User Query: list top 10 invoices with highest amount
SQL Query:  SELECT * FROM ap_invoices ORDER BY invoice_amount DESC FETCH FIRST 10 ROWS ONLY

User Query: show me invoice 908290
SQL query: select * from ap_invoices where invoice_id = '908290'

User Query: show me invoice 300000233136642	
SQL Query: select * from ap_invoices where invoice_id = '300000233136642'

User Query: List the product names, categories, customer names, and promotion names used for sales made in Europe.
SQL Query: SELECT 
    p.prod_name, 
    p.prod_category, 
    c.cust_first_name, 
    c.cust_last_name, 
    pr.promo_name
FROM 
    sales s
JOIN 
    products p ON s.prod_id = p.prod_id
JOIN 
    customers c ON s.cust_id = c.cust_id
JOIN 
    countries co ON c.country_id = co.country_id
JOIN 
    promotions pr ON s.promo_id = pr.promo_id
WHERE 
    co.country_region = 'Europe'

User Query: Get the list of promotion names, customer names, cities, and regions for each sale made in Europe.
SQL Query: SELECT
    pr.promo_name,
    c.cust_first_name||' '||c.cust_last_name AS customer_name,
    c.cust_city,
    co.country_region
FROM
    sales s
JOIN
    promotions pr ON s.promo_id = pr.promo_id
JOIN
    customers c ON s.cust_id = c.cust_id
JOIN
    countries co ON c.country_id = co.country_id
WHERE
    co.country_region = 'Europe'

"""

PROMPT_TEMPLATE = f"""
You are an Oracle SQL expert. 
Given a schema, a user query, and a few examples, generate the appropriate SQL query.
Extract from the user query only the information relevant to generate a correct SQL statement.
Note that the target database is an Oracle database, so ensure the SQL query adheres to Oracle standards and syntax.
Identify first all the tables you need to put in join, then all the needed columns and finally write the SQL.
Don't use the LIMIT N clause, instead, replace it by FETCH FIRST N ROWS ONLY.
Manage correcty dates using the TO_DATE function.
Don't use the CONCAT function for string concatenation. Use instead the || operator.
Enclose the SQL generated with triple backtick always.
If the User Group Id has a value add the proper filter conditions to the query only for tables
containing USER_GROUP_ID as a column.

Examples:
{EXAMPLES}

Schema:
{{schema}}

User Query:
{{query}}

User Group Id:
{{user_group_id}}

SQL Query:
"""

PROMPT_CORRECTION_TEMPLATE = f"""
You are an Oracle SQL expert. 
Given a schema, a user query, a few examples, a SQL query with an error generate the corrected SQL query.
Note that the target database is an Oracle database, so ensure the SQL query adheres to Oracle standards and syntax.
Identify first all the tables you need to put in join, then all the needed columns and finally write the SQL.
Don't use the LIMIT N clause, instead, replace it by FETCH FIRST N ROWS ONLY.
Manage correcty dates using the TO_DATE function.
Don't use the CONCAT function for string concatenation. Use instead the || operator.
Enclose the SQL generated with triple backtick always.

Examples:
{EXAMPLES}

Schema:
{{schema}}

User Query:
{{query}}

SQL query and error:
{{sql_and_error}}

Corrected SQL Query:
"""

PROMPT_TABLE_SUMMARY = """You are a data analyst that can help summarize SQL tables.

Summarize below table by the given context.

Table Schema
{table_schema}

Sample Queries
{sample_queries}

Response guideline
 - You shall write the summary based only on provided information.
 - Note that above sampled queries are only small sample of queries and thus not all possible use of tables are represented, 
   and only some columns in the table are used.
 - Do not use any adjective to describe the table. For example, the importance of the table, its comprehensiveness or 
   if it is crucial, or who may be using it. For example, you can say that a table contains certain types of data, 
   but you cannot say that the table contains a 'wealth' of data, or that it is 'comprehensive'.
 - Do not mention about the sampled query. Only talk objectively about the type of data the table contains and its possible utilities.
 - Please also include some potential usecases of the table, e.g. what kind of questions can be answered by the table, 
 what kind of analysis can be done by the table, etc.

 Table Summary:
"""
