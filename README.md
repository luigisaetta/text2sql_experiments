# Text2SQL experiments 
This repository contains some experiments on using LLM for Text2SQL

This code is for my personal learning and experiments. 
You can take it for the same purpouses, but please, don't expect support from me now.
In addition, the code is changing frequently.

## Notes
* for now the code has been tested only with **ADB**
* in V2 the schema has been partitioned by tables. We store tables summaries in a Vector Store
and apply similarity search.

## References
* [Pinterest Text2SQL](https://medium.com/pinterest-engineering/how-we-built-text-to-sql-at-pinterest-30bad30dabff)

## Tests
Test programs have been moved to the **tests** directory.

To run a test, from the root of the project:

1. Set the python path (see script)
2. Run with a command line like the following

python tests/test_vector_db_connection.py 
