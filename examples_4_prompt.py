"""
This file contains all the examples to be used in the prompt for SQL generation
"""

# the list of few shot examples is here
EXAMPLES = """"
User Query: give me examples of questions I can ask about our data
SQL Query: SELECT t.table_name, c.column_name FROM user_tables t JOIN user_tab_columns c
ON t.table_name = c.table_name ORDER BY t.table_name, c.column_id

User Query: Describe table SALES
SQL Query: SELECT column_name, data_type FROM user_tab_columns WHERE table_name = 'SALES'

User Query: describe the sales table, list all available columns
SQL Query: SELECT column_name, data_type FROM user_tab_columns WHERE table_name = 'SALES'

User Query: Describe table CUSTOMERS
SQL Query: SELECT column_name, data_type FROM user_tab_columns WHERE table_name = 'CUSTOMERS'

User Query: show the names of all employees who registered absences started in 2018 and the total hours reported
SQL Query: SELECT e.emp_name, SUM(f.hours_duration) AS total_hours 
FROM F_ABSENCE f JOIN D_EMPLOYEE e ON f.employee_wid = e.dw_key_id 
WHERE f.absence_start_indicator = 'Y' AND f.absence_dt_wid >= 20180101 
AND f.absence_dt_wid < 20190101 GROUP BY e.emp_name ORDER BY total_hours DESC

"""
