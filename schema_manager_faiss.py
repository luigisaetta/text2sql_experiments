"""
Schema Manager FAISS

handle the similarity search to find TOP_N candidate tables
to execute the query and return the portion of schema 
relevant to answer to the query

number of tables is limited to TOP_N (see config)

"""

from langchain_community.vectorstores import FAISS
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit

from schema_manager import SchemaManager
from config import TOP_N, DEBUG


class SchemaManagerFaiss(SchemaManager):
    """
    To handle schema metadata and similarity search
    """

    def init_schema_manager(self):
        """
        Initializes the SchemaManager.

        """
        # init lists
        try:
            llm1 = self.llm_manager.llm_models[0]

            self.logger.info("Reading schema from DB...")

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
            self.db = FAISS.from_documents(docs, self.embed_model)

            self.logger.info("SchemaManager initialisation done!")

        except Exception as e:
            self.logger.error("Error in init Schema Manager !!!")
            self.logger.error(e)

    def get_restricted_schema(self, query):
        """
        Returns the portion of the schema relevant to the user query, based on similarity search.
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
        return restricted_schema
