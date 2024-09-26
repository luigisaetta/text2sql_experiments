"""
Prompts

examples moved to a separate file
"""

# these are the few shot examples
from examples_4_prompt import EXAMPLES

#
# This is the template used for geneartion of ai interpretation and code
#
# improved (9/9/2024)
REPHRASE_PROMPT = """
User has made an initial request, reported below.

User request:
 {user_request}

A SQL query has been executed to retrieve relevant data.

Data retrieved from database:
 {data}

Explain the provided data in a clear and human understandable format.
Be assertive.
Format response in markdown.

## Plotting instructions
If and only the request asks for plotting, or to generate the code for plotting,  
generate the correct Python code to plot the data using matplotlib library.
Align labels at 90 degrees.
If the request doesn't ask for plotting or generating code, don't add any comments, 
simply do not generate the code.
"""

#
# This is the template for the prompt used to generate the SQl query
#
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

#
# This is a template that could be used for prompt for correction
#
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

#
# This is the prompt used to create the summary for each table of the data schema
#
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

#
# This is the prompt used to rerank the list of candidate table for SQL query
#
PROMPT_RERANK = """
You are a data scientist that can help select the most relevant tables for SQL query tasks.

Please select the most relevant table(s) that can be used to generate SQL query for the question.

===Response Guidelines
- Only return the most relevant table(s).
- Return at most {top_n} tables.
- Response should be a valid JSON array of table names which can be parsed by Python json.loads(). For a single table, the format should be ["table_name"].
- enclose always the array in triple backtick, don't start with 'json'

===Tables
{table_schemas}

===Question
{question}
"""
