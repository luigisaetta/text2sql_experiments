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
from langchain_core.prompts import PromptTemplate
from langchain.docstore.document import Document
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit

from prompt_template import PROMPT_TABLE_SUMMARY
from config import DEBUG

SAMPLES_FILE = "sample_queries.json"


class SchemaManager(ABC):
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
        self.db_manager = db_manager
        self.llm_manager = llm_manager
        self.logger = logger

    @abstractmethod
    def init_schema_manager(self):
        """ "
        to be implemented
        """

    def _get_raw_schema(self):
        """
        Connect to data DB and get raw DB schema
        """
        llm1 = self.llm_manager.llm_models[0]

        toolkit = SQLDatabaseToolkit(db=SQLDatabase(self.db_manager.engine), llm=llm1)
        raw_schema = toolkit.get_context()

        return raw_schema

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

                        # create the summary for the table
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
        llm1 = self.llm_manager.llm_models[0]
        summary_chain = table_summary_prompt | llm1

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
            self.logger.error("Error reading and storing sample queries...")
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

    def _find_chunk_by_table_name(self, table_name):
        """
        Finds the chunk of schema corresponding to the given table name.
        """
        # loop in the dictionary list
        for entry in self.tables_chunk:
            if entry["table"] == table_name:
                return entry["chunk"]
        return None

    @abstractmethod
    def get_restricted_schema(self, query):
        """
        Returns the portion of the schema relevant to the user query, based on similarity search.

        query: the user request in NL

        to be implemented
        """
