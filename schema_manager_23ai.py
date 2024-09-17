"""
Schema Manager23AI

specializes the class SchemaManager to use 23AI as VS

handle the similarity search to find TOP_N candidate tables
to execute the query and return the portion of schema 
relevant to answer to the query

number of tables is limited to TOP_N (see config)
"""

import oracledb
from langchain_community.vectorstores.oraclevs import OracleVS
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit

from schema_manager import SchemaManager
from config import TOP_N, DEBUG, CONNECT_ARGS_VECTOR, VECTOR_TABLE_NAME


class SchemaManager23AI(SchemaManager):
    """
    To handle schema metadata and similarity search
    """

    # init defined in the superclass

    def init_schema_manager(self):
        """
        Initializes the SchemaManager.

        reload the data in the Schema Manager DB
        """
        try:
            self.logger.info("Reading schema from DB...")

            llm1 = self.llm_manager.llm_models[0]
            toolkit = SQLDatabaseToolkit(
                db=SQLDatabase(self.db_manager.engine), llm=llm1
            )
            raw_schema = toolkit.get_context()

            # split the schema for tables
            tables = raw_schema["table_info"].split("CREATE TABLE")

            # read the samples queries for each table and
            # create the structure with table_name, sample_queries
            tables_dict = self._read_samples_query()

            # populate summaries and tables_list
            self._process_schema(tables, tables_dict)

            # sanity check
            assert len(self.summaries) == len(self.tables_list)

            # prepare the docs to be embedded
            docs = self._prepare_documents()

            # init the vector store
            self.logger.info("Loading in Oracle 23AI...")

            conn = self._get_db_connection()

            # reload all the tables and schemas in vector store
            # replacing old data
            OracleVS.from_documents(
                docs,
                self.embed_model,
                table_name=VECTOR_TABLE_NAME,
                client=conn,
                distance_strategy=DistanceStrategy.COSINE,
            )

            self.logger.info("SchemaManager initialisation done!")

            conn.close()

        except Exception as e:
            self.logger.error("Error in init Schema Manager !!!")
            self.logger.error(e)

    def _get_db_connection(self):
        """
        get a connection to ADB
        """
        conn = oracledb.connect(**CONNECT_ARGS_VECTOR)

        return conn

    def get_restricted_schema(self, query):
        """
        Returns the portion of the schema relevant to the user query, based on similarity search.

        query: the user request in NL
        """
        # find TOP_N table summaries closer to query
        # this way we identify relevant tables for the query
        try:
            conn = self._get_db_connection()

            v_store = OracleVS(
                conn,
                self.embed_model,
                table_name=VECTOR_TABLE_NAME,
                distance_strategy=DistanceStrategy.COSINE,
            )

            results = v_store.similarity_search(query, k=TOP_N)

            conn.close()

            # now generate the portion of schema with the retrieved tables
            restricted_schema_parts = []

            self.logger.info("Identifying relevant tables for query...")
            for doc in results:
                table_name = doc.metadata.get("table")
                self.logger.info("- %s", table_name)

                # retrieve the portion of schema for the table
                table_chunk = doc.metadata.get("table_chunk")

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
        except Exception as e:
            self.logger.error("Error in get_restricted_schema...")
            self.logger.error(e)
            restricted_schema = ""

        return restricted_schema
