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

User Query: I need a report with all the absences registered in 2017. 
For every department I want employee who have registered absences, the absence type name and the total hours 
reported for each absence type.
SQL Query: SELECT d_dept.department_name, d_emp.emp_name, d_absence_type.absence_type_name, SUM(f_absence.hours_duration) 
AS total_hours_reported FROM F_ABSENCE f_absence JOIN D_EMPLOYEE d_emp ON f_absence.employee_wid = d_emp.dw_key_id 
JOIN D_DEPARTMENT d_dept ON f_absence.dept_wid = d_dept.dw_key_id JOIN D_ABSENCE_TYPE d_absence_type 
ON f_absence.absence_type_wid = d_absence_type.dw_key_id WHERE f_absence.absence_dt_wid >= 20170101 
AND f_absence.absence_dt_wid < 20180101 GROUP BY d_dept.department_name, d_emp.emp_name, d_absence_type.absence_type_name 
ORDER BY d_dept.department_name, total_hours_reported DESC

"""
