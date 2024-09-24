"""
Database Manager
"""

from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError


class DatabaseManager:
    """
    This class handle all the database-related operations
    """

    def __init__(self, connect_args, logger):
        self.connect_args = connect_args
        self.logger = logger
        self.engine = self.create_engine()

    def create_engine(self):
        """
        create the DB engine

        for ADB connection needs wallet and tnsnames
        """
        try:
            self.logger.info("Connecting to the Database...")

            engine = create_engine(
                "oracle+oracledb://:@",
                thick_mode=False,
                connect_args=self.connect_args,
            )
            self.logger.info("DB engine created...")

            return engine

        except SQLAlchemyError as db_err:
            self.logger.error("Error in DatabaseManager:create_engine...")
            self.logger.error("Database connection failed: %s", db_err)
            return None
        except Exception as e:
            self.logger.error("Error in DatabaseManager:create_engine...")
            self.logger.error("Generic Error setting up SQLDatabase: %s", e)
            return None

    def test_query_syntax(self, sql_query):
        """
        check the SQL syntax against the DB
        """
        try:
            with self.engine.connect() as connection:
                connection.execute(text(sql_query))
            return True

        except SQLAlchemyError as db_err:
            self.logger.error("Error in DatabaseManager:test_query_sintax...")
            self.logger.error("SQL query syntax error: %s", db_err)
            return False
        except Exception as e:
            self.logger.error("Error in DatabaseManager:test_query_sintax...")
            self.logger.error("SQL query generic error: %s", e)
            return False

    def execute_sql(self, sql_query):
        """
        execute the given SQL and return a set of rows
        """
        try:
            with self.engine.connect() as connection:
                rows = connection.execute(text(sql_query)).mappings().all()

                self.logger.info("Found %s rows..", len(rows))

                return rows
        except SQLAlchemyError as db_err:
            self.logger.error("Error in DatabaseManager:execute_sql...")
            self.logger.error("SQL query execution error: %s", db_err)
            return None
        except Exception as e:
            self.logger.error("Error in DatabaseManager:execute_sql...")
            self.logger.error("Generic Error executing SQL query: %s", e)
            return None

    #
    # to get a list of tables whose names starts with PREFIX
    #
    def get_tables_list(self, prefix):
        """
        prefix: the initial part of the name of the table
        """
        with self.engine.connect() as connection:
            query = (
                f"SELECT TABLE_NAME FROM USER_TABLES WHERE TABLE_NAME LIKE '{prefix}%'"
            )

            rows = connection.execute(text(query)).mappings().all()

            tables = [table_dict["table_name"] for table_dict in rows]

        return tables
