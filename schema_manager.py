"""
Schema Manager

handle the similarity search to find TOP_N candidate tables
to execute the query and return the portion of schema 
relevant to answer to the query

number of tables is limited to TOP_N (see config)
"""

import re
import json
from langchain_core.prompts import PromptTemplate
from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit

from prompt_template import PROMPT_TABLE_SUMMARY
from config import TOP_N, DEBUG

SAMPLES_FILE = "sample_queries.json"


class SchemaManager:
    """
    To handle schema metadata and similarity search
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
        self.logger = logger

        # this is the prompt used to generate a summary for each table
        # the summary is embedded
        table_summary_prompt = PromptTemplate.from_template(PROMPT_TABLE_SUMMARY)
        llm1 = llm_manager.llm_models[0]

        self.summary_chain = table_summary_prompt | llm1

        # init lists
        try:
            logger.info("Reading schema from DB...")
            toolkit = SQLDatabaseToolkit(db=SQLDatabase(db_manager.engine), llm=llm1)
            raw_schema = toolkit.get_context()

            # split the schema for tables
            tables = raw_schema["table_info"].split("CREATE TABLE")

            # create the structure with table_name, sample_queries
            tables_dict = self._read_samples_query()

            # populate summaries and tables_list
            self._process_schema(tables, tables_dict)

            # sanity check
            assert len(self.summaries) == len(self.tables_list)

            # prepare the docs to be embedded
            docs = self._prepare_documents()

            # init the vector store
            self.db = FAISS.from_documents(docs, embed_model)

        except Exception as e:
            logger.error("Error in init Schema Manager !!!")
            logger.error(e)

    def _process_schema(self, tables, tables_dict):
        """
        populate:
        self.tables_list
        self.tables_chunk
        self.summaries
        """
        try:
            self.tables_list = []
            # in this list we store the chunk of schema for each table
            self.tables_chunk = []
            self.summaries = []

            for table_chunk in tables:
                # check that it is not an empty string
                if table_chunk.strip():
                    match = re.search(r"^\s*([a-zA-Z_][\w]*)\s*\(", table_chunk)

                    if match:
                        table_name = match.group(1)

                        # normalize all table names in capital letters
                        table_name = table_name.upper()
                        self.logger.info("Table name: %s", table_name)

                        self.tables_list.append(table_name)

                        table_chunk = "CREATE TABLE " + table_chunk
                        self.tables_chunk.append(
                            {"table": table_name, "chunk": table_chunk}
                        )

                        sample_queries = self.get_sample_queries(
                            table_name, tables_dict
                        )["sample_queries"]

                        summary = self._generate_table_summary(
                            table_chunk, sample_queries
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

        The summary is generetaed using:
        - the portion of the schema related to the table
        - a slit of sample queries
        """
        result = self.summary_chain.invoke(
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

        return tables_dict

    def get_sample_queries(self, table_name, data):
        """
        return a list of sample queries for the given table

        table_name: the name of the table (UPPERCASE)
        data: the dictionary read from file samples_query.json
        """
        return data.get(table_name, None)

    def _prepare_documents(self):
        """
        Prepares documents containing table names and summaries for vector search.
        """
        docs = []
        for table_name, summary in zip(self.tables_list, self.summaries):
            # this is the content embedded
            content = table_name + "\nSummary:\n" + summary
            docs.append(Document(page_content=content, metadata={"table": table_name}))
        return docs

    def _find_chunk_by_table_name(self, table_name):
        """
        Finds the chunk of schema corresponding to the given table name.
        """
        # loop in the dictionary list
        for entry in self.tables_chunk:
            if entry["table"] == table_name:
                return entry["chunk"]
        return None

    def get_restricted_schema(self, query):
        """
        Returns the portion of the schema relevant to the user query based on similarity search.
        """

        # find TOP_N table summaries closer to query
        # this way we identify relevant tables for the query
        results = self.db.similarity_search(query, k=TOP_N)

        # now generate the portion of schema with the retrieved tables
        restricted_schema_parts = []

        self.logger.info("Identifying relevant tables for query...")
        for doc in results:
            table_name = doc.metadata.get("table")
            self.logger.info("Found table: %s", table_name)

            # retrieve the portion of schema relevant to the table
            table_chunk = self._find_chunk_by_table_name(table_name)
            if table_chunk:
                restricted_schema_parts.append(table_chunk)
            else:
                self.logger.warning("No chunk found for table %s", table_name)

        # Join the accumulated chunks into a single string
        # this is the schema relevant to generate the SQL
        # associated to the user query
        restricted_schema = "".join(restricted_schema_parts)

        if DEBUG:
            self.logger.info(restricted_schema)
        return restricted_schema
