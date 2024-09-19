"""
Encapsulate the entire AI SQL Agent to simplify its usage

Author: L. Saetta (Oracle)
        19/09/2024
        v 0.95
"""

from langchain_community.embeddings import OCIGenAIEmbeddings

from core_functions import generate_sql_with_models
from database_manager import DatabaseManager
from llm_manager import LLMManager
from schema_manager_23ai import SchemaManager23AI

from utils import get_console_logger


class AISQLAgent:
    """
    Wraps all the code needed to use the SQL Agent
    """

    def __init__(
        self,
        connect_args,
        model_list,
        endpoint,
        compartment_ocid,
        embed_model_name,
        temperature,
        prompt_template,
    ):
        """
        Initialize the AI SQL Agent with required configurations.

        Args:
            connect_args (dict): Database connection arguments to connect to DATA DB.
            model_list (list): List of LLM models to use.
            endpoint (str): Service endpoint for the AI models.
            compartment_ocid (str): Compartment OCID for Oracle Cloud Infrastructure.
            embed_model_name (str): Embedding model name.
            temperature (float): Temperature setting for the LLM manager.
            prompt_template (str): Template for generating SQL queries.
        """
        # store information needed
        self.connect_args = connect_args
        self.model_list = model_list
        self.endpoint = endpoint
        self.compartment_ocid = compartment_ocid
        self.embed_model_name = embed_model_name
        self.temperature = temperature
        self.prompt_template = prompt_template

        # Initialize components
        self.logger = get_console_logger()

        self.db_manager = self._initialize_db_manager()
        self.llm_manager = self._initialize_llm_manager()
        self.embed_model = self._initialize_embed_model()
        self.schema_manager = self._initialize_schema_manager()

        self.logger.info("AI SQL Agent initialized successfully.")

    def _initialize_db_manager(self):
        """Initialize the DatabaseManager with connection arguments and logger."""
        return DatabaseManager(self.connect_args, self.logger)

    def _initialize_llm_manager(self):
        """Initialize the LLMManager with model list, endpoint, and temperature."""
        return LLMManager(
            self.model_list,
            self.endpoint,
            self.compartment_ocid,
            self.temperature,
            self.logger,
        )

    def _initialize_embed_model(self):
        """Initialize the embedding model for schema manager."""
        return OCIGenAIEmbeddings(
            model_id=self.embed_model_name,
            service_endpoint=self.endpoint,
            compartment_id=self.compartment_ocid,
        )

    def _initialize_schema_manager(self):
        """Initialize the SchemaManager23AI with required components."""
        self.logger.info("Loading Schema Manager...")

        return SchemaManager23AI(
            self.db_manager, self.llm_manager, self.embed_model, self.logger
        )

    def generate_restricted_schema(self, user_request):
        """
        Generate a restricted schema based on the user request.

        Args:
            user_request (str): The user’s SQL query request.

        Returns:
            dict: The restricted schema for the SQL query.
        """
        self.logger.info("Generating restricted schema for user request...")

        restricted_schema = self.schema_manager.get_restricted_schema(user_request)

        self.logger.info("Restricted schema generated.")

        return restricted_schema

    def generate_sql_query(self, user_request):
        """
        Generate the SQL query based on the user request and restricted schema.

        Args:
            user_request (str): The user’s SQL query request.

        Returns:
            str: The generated SQL query.
        """
        restricted_schema = self.generate_restricted_schema(user_request)

        self.logger.info("Generating SQL query...")

        sql_query = generate_sql_with_models(
            user_request,
            restricted_schema,
            self.db_manager,
            self.llm_manager,
            self.prompt_template,
        )
        self.logger.info("SQL query generated.")

        return sql_query
