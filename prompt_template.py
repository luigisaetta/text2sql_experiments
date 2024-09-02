"""
Prompts and examples
"""

REPHRASE_PROMPT = """Please rephrase the following response and don't respond
in the response as 'Here is a rephrased version of the response' : {response}"""

# the list of few shot examples is here
EXAMPLES = """"
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
    c.cust_first_name||' '||c.cust_last_name) AS customer_name,
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
