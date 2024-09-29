"""
Schema Manager 23AI

This module extends the SchemaManager class to integrate 
with 23AI as a Vector Store (VS).
It handles the similarity search to find the TOP_N candidate 
tables in a schema, executes the query, and returns 
the relevant portion of the schema necessary to answer the query.

The number of candidate tables is limited to TOP_N 
(configurable in the settings).
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
    # the name of the table from where we get the samples queries
    TABLE_NAME_SQ,
    INCLUDE_TABLES_PREFIX,
)


class SchemaManager23AI(SchemaManager):
    """
    Specialized class for managing schema metadata 
    and performing similarity searches using the 
    23AI Vector Store system.

    Inherits from SchemaManager to extend 
    its functionality with 23AI capabilities.
    """

    # init defined in the superclass

    def init_schema_manager(self):
        """
        Initializes the Schema Manager by loading the schema data 
        into the Schema Manager database.

        This method reads the schema information from the database,
        processes the table chunks, and optionally filters them based 
        on the prefix defined by INCLUDE_TABLES_PREFIX.

        Raises:
            Exception: If the schema cannot be loaded.
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

            # reload all the tables and schemas in vector store
            # replacing old data
            with self._get_vector_db_connection() as conn:
                OracleVS.from_documents(
                    docs,
                    self.embed_model,
                    table_name=VECTOR_TABLE_NAME,
                    client=conn,
                    distance_strategy=DISTANCE_STRATEGY,
                )

            self.logger.info("SchemaManager initialisation done!")

        except Exception as e:
            self._handle_exception(e, "Error in SchemaManager:init_schema_manager...")

    def delete_from_schema_manager(self, conn, t_name):
        """
        Delete the record for a selected table from the VECTOR tables
        """
        try:
            # Create a cursor object
            cursor = conn.cursor()

            # SQL statement to delete a record where t_name matches
            sql = f"""DELETE FROM {VECTOR_TABLE_NAME} WHERE
                   json_value(METADATA, '$.table') = :t_name_value
                   """

            # Execute the DELETE SQL with the value of t_name
            cursor.execute(sql, {"t_name_value": t_name})

        except Exception as e:
            self._handle_exception(
                e, "Error in SchemaManager:delete_from_schema_manager..."
            )

    def update_schema_manager(self, selected_tables_list):
        """
        Update the data for selected tables in the Schema Manager DB

        update does delete and insert
        """
        self.logger.info("Selected tables: %s", selected_tables_list)

        try:
            self.logger.info("Reading schema from DB...")

            raw_schema = self._get_raw_schema()

            # split the schema for tables
            # tables is a list of table chunk (chunks of schema desc)
            tables = raw_schema["table_info"].split("CREATE TABLE")

            # filter chunks
            # take only those whose tables are in selected table list
            # starting from tables we avoid mistakes in the tables list
            tables = [
                t_chunk
                for t_chunk in tables
                if self._get_table_name_from_table_chunk(t_chunk).upper()
                in selected_tables_list
            ]

            # read the samples queries for each table and
            # create the structure with table_name, sample_queries
            tables_dict = self._read_samples_query()

            # populate summaries and tables_list
            self._process_schema(tables, tables_dict)

            # prepare the docs to be embedded, only for selected tables
            docs = self._prepare_documents()

            # update the vector store
            self.logger.info("Updating Oracle 23AI...")

            with self._get_vector_db_connection() as conn:
                # delete record in vector store for selected tables
                for doc in docs:
                    self.logger.info(" Deleting %s", doc.metadata["table"])
                    self.delete_from_schema_manager(conn, doc.metadata["table"])

                # loading
                self.logger.info("Saving new records to Vector Store...")

                v_store = OracleVS(
                    client=conn,
                    table_name=VECTOR_TABLE_NAME,
                    distance_strategy=DISTANCE_STRATEGY,
                    embedding_function=self.embed_model,
                )
                v_store.add_documents(docs)

                self.logger.info("Processed %s tables...", len(docs))
                self.logger.info("")
                self.logger.info("SchemaManager update done!")

                # end the transaction
                conn.commit()

        except Exception as e:
            self._handle_exception(e, "Error in SchemaManager:update_schema_manager...")

    def _read_samples_query(self):
        """
        Reads sample queries from the DB.
        """
        self.logger.info("")
        self.logger.info("Reading sample queries...")

        select_query = f"SELECT table_name, sample_query FROM {TABLE_NAME_SQ}"
        # Create the target structure
        tables_dict = {}

        try:
            with self._get_vector_db_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(select_query)

                # loop over all rows
                for table_name, sample_query in cursor:
                    # Normalize table name in upper case
                    table_name = table_name.upper()

                    # add sample query in the list in dictiornary
                    if table_name in tables_dict:
                        tables_dict[table_name]["sample_queries"].append(sample_query)
                    else:
                        tables_dict[table_name] = {"sample_queries": [sample_query]}

                cursor.close()

            self.logger.info("Sample queries read successfully.")

        except oracledb.DatabaseError as e:
            self._handle_exception(e, "Error in SchemaManager:read_samples_query...")

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
            with self._get_vector_db_connection() as conn:

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
            self._handle_exception(e, "Error in SchemaManager:get_restricted_schema...")
            restricted_schema = ""

        return restricted_schema

    #
    # Resource management and helper functions
    #
    #
    # better exception logging
    #
    def _handle_exception(self, e, context: str = ""):
        """Log the exception and provide context."""
        self.logger.error("Error in %s: %s", context, e)

    def _get_vector_db_connection(self):
        """Return a database connection to the vector store."""
        return oracledb.connect(**CONNECT_ARGS_VECTOR)
