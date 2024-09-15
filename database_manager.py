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

        for ADB connection needs wallet and tnsnames configured
        """
        try:
            self.logger.info("Connecting to the Database...")

            engine = create_engine(
                "oracle+oracledb://:@",
                thick_mode=False,
                connect_args=self.connect_args,
            )
            self.logger.info("Connected, DB engine created...")

            return engine

        except SQLAlchemyError as db_err:
            self.logger.error("Database connection failed: %s", db_err)
            return None
        except Exception as e:
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
            self.logger.error("SQL query syntax error: %s", db_err)
            return False
        except Exception as e:
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
            self.logger.error("SQL query execution error: %s", db_err)
            return None
        except Exception as e:
            self.logger.error("Generic Error executing SQL query: %s", e)
            return None
