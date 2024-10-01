"""
Schema Manager

handle the similarity search to find TOP_N candidate tables
to execute the query and return the portion of schema 
relevant to answer to the query

number of tables is limited to TOP_N (see config)

this is an abstract class
"""

import re
import json
from abc import ABC, abstractmethod
from tqdm import tqdm
import oracledb
from langchain_core.prompts import PromptTemplate
from langchain.docstore.document import Document

from prompt_template import PROMPT_TABLE_SUMMARY, PROMPT_RERANK
from config import (
    CONNECT_ARGS,
    DEBUG,
    TOP_N,
    N_SAMPLES,
    INDEX_MODEL_FOR_RERANKING,
    INDEX_MODEL_FOR_SUMMARY,
)
from config_private import DB_USER

SAMPLES_FILE = "sample_queries.json"


class SchemaManager(ABC):
    """
    To handle schema metadata and similarity search

    this is an abstract class... must be implemented
        It is abstract since it is not tied to a specific vector store
        but it is specialized to use Oracle as data store
    """

    def __init__(self, db_manager, llm_manager, embed_model, logger):
        """
        Initializes the SchemaManager.

        db_manager: Manages the database connection.
        llm_manager: Manages the LLM models.
        embed_model: Embedding model to be used.
        logger: Logger instance.
        """
        self.embed_model = embed_model
        self.db_manager = db_manager
        self.llm_manager = llm_manager
        self.logger = logger

    @abstractmethod
    def init_schema_manager(self):
        """ "
        Abstract method to be implemented by subclasses to initialize schema management logic.
        """

    @abstractmethod
    def get_restricted_schema(self, query):
        """
        Returns the portion of the schema relevant to the user query, based on similarity search.

        query: the user request in NL

        to be implemented
        """

    def _get_raw_schema(self, schema_owner=DB_USER, n_samples=N_SAMPLES):
        """
        This is the new code (no LangChain for schema)
        Connect to data DB and get raw DB schema

        This function reads metadata and sample data for each table
        """
        conn = oracledb.connect(**CONNECT_ARGS)

        # the dict that will contain the raw schema
        output_dict = {"table_info": "", "table_names": ""}

        try:
            # Create a cursor object
            cursor = conn.cursor()

            # to simplify DDL generation removing info not needed
            cursor.execute(
                """
                BEGIN
                    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 
                    'STORAGE', FALSE);
                    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 
                    'TABLESPACE', FALSE);
                    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 
                    'SEGMENT_ATTRIBUTES', FALSE);
                    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 
                    'CONSTRAINTS_AS_ALTER', TRUE);
                END;
            """
            )

            # Query to get the table names sorted alphabetically
            query = """
                SELECT table_name
                FROM all_tables
                WHERE owner = :schema_owner
                ORDER BY table_name
            """

            # Execute the query
            cursor.execute(query, schema_owner=schema_owner)

            # Fetch all table names
            tables = cursor.fetchall()

            # to memorize all the tables
            table_names = []

            # Iterate through each table and get its CREATE TABLE statement
            for table in tqdm(tables):
                table_name = table[0]
                table_names.append(table_name)

                # Use DBMS_METADATA to generate the CREATE TABLE statement
                cursor.execute(
                    f"""
                    SELECT DBMS_METADATA.GET_DDL('TABLE', '{table_name}', '{schema_owner}')
                    FROM dual
                """
                )

                # Fetch the DDL
                ddl_lob = cursor.fetchone()[0]

                # Remove the collate clauses
                # Convert LOB to string
                ddl = ddl_lob.read() if isinstance(ddl_lob, oracledb.LOB) else ddl_lob
                ddl_cleaned = ddl.replace('COLLATE "USING_NLS_COMP"', "")
                ddl_cleaned = ddl_cleaned.replace(
                    'DEFAULT COLLATION "USING_NLS_COMP"', ""
                )
                # remove schema from ddl
                ddl_cleaned = ddl_cleaned.replace(f'"{schema_owner}".', "")
                # remove "
                ddl_cleaned = ddl_cleaned.replace('"', "")

                # Build output for table info
                table_info = f"{ddl_cleaned}\n\n"

                # ADD COLUMN COMMENTS
                cursor.execute(
                    """
                    SELECT column_name, comments
                    FROM all_col_comments
                    WHERE owner = :schema_owner AND table_name = :table_name
                    """,
                    schema_owner=schema_owner,
                    table_name=table_name,
                )
                column_comments = cursor.fetchall()

                if column_comments:
                    table_info += "--- Column Comments ---\n"
                    for column_name, comment in column_comments:
                        if comment:
                            table_info += f"Column {column_name}: {comment}\n"
                    table_info += "\n"

                if DEBUG:
                    self.logger.info(table_info)

                # add output to dict
                output_dict["table_info"] += table_info

                # Query to get the first 3 records from the table
                try:
                    cursor.execute(
                        f"""SELECT * FROM {schema_owner}.{table_name} 
                        FETCH FIRST {n_samples} ROWS ONLY"""
                    )
                    records = cursor.fetchall()

                    # Get the column names for better formatting
                    columns = [col[0] for col in cursor.description]

                    # output for records
                    records_info = (
                        f"--- First {n_samples} records from {table_name} ---\n"
                    )
                    if records:
                        # add columns headers
                        records_info += " | ".join(columns) + "\n"

                        # add records
                        for record in records:
                            records_info += str(record) + "\n"
                    else:
                        records_info += f"No records found in {table_name}\n"

                    if DEBUG:
                        self.logger.info(records_info)

                    # add output to dict
                    output_dict["table_info"] += records_info + "\n"

                except Exception as e:
                    error_message = f"Error retrieving records from {table_name}: {e}\n"
                    self.logger.error(error_message)
                    # add nothings
                    output_dict["table_info"] += "\n"

            # add table names comma separated
            output_dict["table_names"] = ", ".join(table_names)

        except Exception as e:
            self.logger.error("Error: %s", e)

        finally:
            # Close the cursor
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        return output_dict

    def _process_schema(self, tables, tables_dict):
        """
        populate:
        * self.tables_list
        * self.tables_chunk
        * self.summaries
        """
        try:
            self.tables_list = []
            # in this list we store the chunk of schema for each table
            self.tables_chunk = []
            self.summaries = []

            self.logger.info("Processing tables...")

            for table_chunk in tqdm(tables):
                # check that it is not an empty string
                if table_chunk.strip():
                    match = re.search(r"^\s*([a-zA-Z_][\w]*)\s*\(", table_chunk)

                    if match:
                        table_name = match.group(1)

                        # normalize all table names in capital letters
                        table_name = table_name.upper()
                        self.logger.info("Table name: %s", table_name)

                        self.tables_list.append(table_name)

                        # create the summary for the table

                        # remove not needed line (see above)
                        table_chunk = self._remove_compress_line(table_chunk)

                        table_chunk = "CREATE TABLE " + table_chunk
                        self.tables_chunk.append(
                            {"table": table_name, "chunk": table_chunk}
                        )

                        queries_list = self.get_sample_queries(table_name, tables_dict)
                        # concatenate into a single string
                        queries_string = "\n".join(queries_list)

                        summary = self._generate_table_summary(
                            table_chunk, queries_string
                        )

                        self.summaries.append(summary)

                        if DEBUG:
                            self.logger.info("Summary:")
                            self.logger.info(summary)

                    else:
                        self.logger.error("Table name not found !")

        except Exception as e:
            self.logger.error("Error in _process_schema...")
            self.logger.error(e)

    def _generate_table_summary(self, table_chunk, sample_queries):
        """
        Generates a summary for the given table using the LLM.

        The summary is generated using:
        - the portion of the schema related to the table
        - a list of sample queries
        """
        table_summary_prompt = PromptTemplate.from_template(PROMPT_TABLE_SUMMARY)
        llm_s = self.llm_manager.llm_models[INDEX_MODEL_FOR_SUMMARY]
        summary_chain = table_summary_prompt | llm_s

        result = summary_chain.invoke(
            {
                "table_schema": table_chunk,
                "sample_queries": sample_queries,
            }
        )
        return result.content

    def _read_samples_query(self):
        """
        Reads sample queries from the JSON file.
        """
        # read the JSON file with sample queries
        self.logger.info("")
        self.logger.info("Reading sample queries...")

        try:
            with open(SAMPLES_FILE, "r", encoding="UTF-8") as file:
                data = json.load(file)

            # create a dictionary where key is table_name
            # and value is a dict with one field: sample queries
            tables_dict = {}
            for element in data:
                table_name = element.get("table")
                if table_name:
                    # normalize in uppercase
                    table_name = table_name.upper()
                    tables_dict[table_name] = {
                        "sample_queries": element.get("sample_queries")
                    }

            self.logger.info("Reading and storing Sample queries OK...")
        except Exception as e:
            self.logger.error("Error reading sample queries...")
            self.logger.error("Check file: %s", SAMPLES_FILE)
            self.logger.error(e)
            tables_dict = {}

        return tables_dict

    def get_sample_queries(self, table_name, data):
        """
        return a list of sample queries for the given table

        table_name: the name of the table (UPPERCASE)
        data: the dictionary read from file samples_query.json
        """
        if data.get(table_name, None) is not None:
            return data.get(table_name, None)["sample_queries"]
        return []

    def _prepare_documents(self):
        """
        Prepares documents containing table names and summaries for vector search.
        """
        docs = []
        for table_name, summary in zip(self.tables_list, self.summaries):
            # this is the content embedded
            content = table_name + "\nSummary:\n" + summary

            # retrieve table_chunk
            table_chunk = self._find_chunk_by_table_name(table_name)
            # all data stored in Vector Store
            doc = Document(
                page_content=content,
                metadata={"table": table_name, "table_chunk": table_chunk},
            )
            docs.append(doc)
        return docs

    def _rerank_table_list(self, query, top_k_schemas):
        """
        Get TOP_N tables from step1 in schema selection and use an LLM
        to rerank the TOP_N

        query: user query in NL
        top_k_schemas: schemas for top_k tables
        produce a restricted TOP_N list
        """
        # to be implemented and plugged in get_restricted schema
        table_select_prompt = PromptTemplate.from_template(PROMPT_RERANK)

        llm_r = self.llm_manager.llm_models[INDEX_MODEL_FOR_RERANKING]
        rerank_chain = table_select_prompt | llm_r

        result = rerank_chain.invoke(
            {
                "top_n": TOP_N,
                "table_schemas": top_k_schemas,
                "question": query,
            }
        )

        # extract the table list (in result it is surrounded by triple backtick)
        reranked_tables_list = self._extract_list(result.content)

        return reranked_tables_list

    #
    # Resource management and helper functions
    #
    def _get_table_name_from_table_chunk(self, chunk):
        """
        extract only the table name
        """
        table_name = ""

        if chunk.strip():
            match = re.search(r"^\s*([a-zA-Z_][\w]*)\s*\(", chunk)

            if match:
                table_name = match.group(1)
                table_name = table_name.upper()

        return table_name

    def _find_chunk_by_table_name(self, table_name):
        """
        Finds the chunk of schema corresponding to the given table name.
        """
        # loop in the dictionary list
        for entry in self.tables_chunk:
            if entry["table"] == table_name:
                return entry["chunk"]
        return None

    def _extract_list(self, input_string):
        """
        Extract the content between the triple backticks
        Function used by _rerank_table_list
        """
        extracted_string = input_string.strip().strip("`")

        # Remove the square brackets and extra whitespace
        cleaned_string = extracted_string.replace("[", "").replace("]", "").strip()

        # Split the string by commas and remove quotes/extra spaces
        tables_list = [item.strip().strip('"') for item in cleaned_string.split(",")]

        return tables_list

    def _remove_compress_line(self, chunk):
        """ "
        remove the line containing COMPRESS FOR...
        fro the chunk of schema
        to reduce prompt length
        """
        # Split the string into lines
        lines = chunk.splitlines()

        # Filter out the line containing "COMPRESS"
        lines = [line for line in lines if "COMPRESS" not in line]

        # Join the lines back into a single string
        updated_chunk = "\n".join(lines)

        return updated_chunk

    def _close_connection(self, conn):
        """
        close properly the conn

        yes, it is annoying, but we need to do this way

        can be used for data or vector schema connection... that's the reason it is here
        """
        try:
            if conn:
                conn.close()
        except Exception:
            # ignore, connection is closed
            pass
