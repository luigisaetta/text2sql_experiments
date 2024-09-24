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

from schema_manager import SchemaManager
from config import (
    TOP_K,
    CONNECT_ARGS_VECTOR,
    VECTOR_TABLE_NAME,
    DISTANCE_STRATEGY,
    ENABLE_RERANKING,
    TABLE_NAME_SQ,
    INCLUDE_TABLES_PREFIX,
)


class SchemaManager23AI(SchemaManager):
    """
    To handle schema metadata and similarity search
    """

    # init defined in the superclass

    # the table where we store a list of user_queries for each table in the data schema
    # name imported from config
    TABLE_NAME_SQ = TABLE_NAME_SQ

    def init_schema_manager(self):
        """
        Initializes the SchemaManager.

        reload the data in the Schema Manager DB
        """
        try:
            self.logger.info("Reading schema from DB...")

            raw_schema = self._get_raw_schema()

            # split the schema for tables
            # tables is a list of table chunk (chunks of schema desc)
            tables = raw_schema["table_info"].split("CREATE TABLE")

            # added to eventually filter table_names
            if INCLUDE_TABLES_PREFIX != "ALL":
                # takes only those starting with INCLUDE_TABLES_PREFIX
                tables = [
                    t_chunk
                    for t_chunk in tables
                    if self._get_table_name_from_table_chunk(t_chunk)
                    .upper()
                    .startswith(INCLUDE_TABLES_PREFIX)
                ]

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
                distance_strategy=DISTANCE_STRATEGY,
            )

            self.logger.info("SchemaManager initialisation done!")

            conn.close()

        except Exception as e:
            self.logger.error("Error in SchemaManager:init_schema_manager...")
            self.logger.error("Error in init Schema Manager !!!")
            self.logger.error(e)
        finally:
            self._close_connection(conn)

    def _get_db_connection(self):
        """
        get a connection to ADB
        """
        conn = oracledb.connect(**CONNECT_ARGS_VECTOR)

        return conn

    def _close_connection(self, conn):
        """
        close properly the conn

        yes, it is annoying, but we need to do this way
        """
        try:
            if conn:
                conn.close()
        except Exception:
            # ignore, connection is closed
            pass

    def _read_samples_query(self):
        """
        Reads sample queries from the DB.
        """
        self.logger.info("")
        self.logger.info("Reading sample queries...")

        select_query = f"SELECT table_name, sample_query FROM {self.TABLE_NAME_SQ}"

        try:
            conn = self._get_db_connection()

            cursor = conn.cursor()

            cursor.execute(select_query)

            # Create the target structure
            tables_dict = {}

            # loop over all rows
            for table_name, sample_query in cursor:
                # Normalize table name in upper case
                table_name = table_name.upper()

                # add sample query in the list in dictiornary
                if table_name in tables_dict:
                    tables_dict[table_name]["sample_queries"].append(sample_query)
                else:
                    tables_dict[table_name] = {"sample_queries": [sample_query]}

            self.logger.info("Reading and storing Sample queries OK...")

        except oracledb.DatabaseError as e:
            self.logger.error("Error in SchemaManager:read_samples_query...")
            self.logger.error("Error during reading sample queries from DB: %s", e)
            tables_dict = {}
        finally:
            if cursor:
                cursor.close()
            self._close_connection(conn)

        return tables_dict

    def _similarity_search(self, query, conn):
        """
        execute the search for TOP_K tables using 23AI
        """
        v_store = OracleVS(
            conn,
            self.embed_model,
            table_name=VECTOR_TABLE_NAME,
            distance_strategy=DISTANCE_STRATEGY,
        )

        # get TOP_K tables (step1)
        results = v_store.similarity_search(query, k=TOP_K)

        return results

    def get_restricted_schema(self, query):
        """
        Returns the portion of the schema relevant to the user query, based on similarity search.

        query: the user request in NL
        """
        # find TOP_N table summaries closer to query
        # this way we identify relevant tables for the query
        # step1: similarity search: returns TOP_K
        # step2: rerank, using LLM and returns TOP_N
        try:
            conn = self._get_db_connection()

            results = self._similarity_search(query, conn)

            # now generate the portion of schema with the retrieved tables

            # step 1: TOP_K
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
            restricted_schema = "".join(restricted_schema_parts)

            # added this part (20/09) for reranking table list
            if ENABLE_RERANKING and len(restricted_schema) > 0:
                # step2
                restricted_schema2_parts = []
                # rerank  and restrict (call LLM)
                table_top_n_list = self._rerank_table_list(query, restricted_schema)

                self.logger.info("Reranker result:")
                self.logger.info(table_top_n_list)
                self.logger.info("")

                for table_name in table_top_n_list:
                    # find the table chunk
                    for doc in results:
                        if doc.metadata.get("table") == table_name.upper():
                            table_chunk = doc.metadata.get("table_chunk")
                            restricted_schema2_parts.append(table_chunk)
                            break

                restricted_schema = "".join(restricted_schema2_parts)

        except Exception as e:
            self.logger.error("Error in SchemaManager:get_restricted_schema...")
            self.logger.error(e)
            restricted_schema = ""
        finally:
            # This block will always execute, so we ensure the connection is closed
            self._close_connection(conn)

        return restricted_schema
