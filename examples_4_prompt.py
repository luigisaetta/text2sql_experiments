"""
This file contains all the examples to be used in the prompt for SQL generation
"""

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
