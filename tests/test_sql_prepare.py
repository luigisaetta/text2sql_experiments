"""
Test if SQL generated is correct (syntactically)
"""

import oracledb
from config import CONNECT_ARGS

try:
    with oracledb.connect(**CONNECT_ARGS) as conn:
        with conn.cursor() as cursor:

            # This is the SQL instr you want to verify
            sql = "SELECT * FROM EMPLOYEES"
            # sql = "SELECT * FROM EMPLOYEES WHERE COL1 = 2"

            # you ask to create the Execution plan
            explain_sql = f"EXPLAIN PLAN FOR {sql}"

            cursor.execute(explain_sql)

            print("Sintax is OK!")

except oracledb.DatabaseError as e:
    (error,) = e.args
    print("SQL syntax error:", error.message)
