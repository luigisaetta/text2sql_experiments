"""
File name: ai_sql_agent.py
Author: Luigi Saetta
Date last modified: 2024-10-21
Python Version: 3.11

Description:
    Encapsulate the entire AI SQL Agent to simplify its usage

Inspired by:
   
Usage:
    Import this module into other scripts to use its functions. 
    Example:

Dependencies:
    langChain

License:
    This code is released under the MIT License.

Notes:
    This is a part of a set of demos showing how to build a SQL Agent
    for Text2SQL taks

Warnings:
    This module is in development, may change in future versions.
"""

import time
from langchain_community.embeddings import OCIGenAIEmbeddings
from core_functions import clean_sql_query
from database_manager import DatabaseManager
from llm_manager import LLMManager
from schema_manager_23ai import SchemaManager23AI
from request_cache import RequestCache

from utils import get_console_logger
from config import AUTH_TYPE


class AISQLAgent:
    """
    Wraps all the code needed to use the SQL Agent

    5/10: added a simple cache, useful especially for demos
    """

    def __init__(
        self,
        connect_args,
        model_list,
        model_endpoints,
        compartment_ocid,
        embed_model_name,
        embed_endpoint,
        temperature,
        prompt_template,
    ):
        """
        Initialize the AI SQL Agent with required configurations.

        Args:
            connect_args (dict): Database connection arguments to connect to DATA DB.
            model_list (list): List of LLM models to use.
            model_endpoints (list): Service endpoints for the AI models.
            compartment_ocid (str): Compartment OCID for Oracle Cloud Infrastructure.
            embed_model_name (str): Embedding model name.
            temperature (float): Temperature setting for the LLM manager.
            prompt_template (str): Template for generating SQL queries.

        """
        # store information needed
        self.connect_args = connect_args
        self.model_list = model_list
        self.model_endpoints = model_endpoints
        self.compartment_ocid = compartment_ocid
        self.embed_model_name = embed_model_name
        self.embed_endpoint = embed_endpoint
        self.temperature = temperature
        self.prompt_template = prompt_template

        # Initialize components
        self.logger = get_console_logger()

        self.db_manager = self._initialize_db_manager()
        self.llm_manager = self._initialize_llm_manager()
        self.embed_model = self._initialize_embed_model()
        self.schema_manager = self._initialize_schema_manager()

        # added for an exact cache
        self.request_cache = RequestCache()

        self.logger.info("AI SQL Agent initialized successfully.")

    def _initialize_db_manager(self):
        """Initialize the DatabaseManager with connection arguments and logger."""
        return DatabaseManager(self.connect_args, self.logger)

    def _initialize_llm_manager(self):
        """Initialize the LLMManager with model list, endpoints, and temperature."""
        return LLMManager(
            self.model_list,
            self.model_endpoints,
            self.compartment_ocid,
            self.temperature,
            self.logger,
        )

    def _initialize_embed_model(self):
        """Initialize the embedding model for schema manager."""
        return OCIGenAIEmbeddings(
            auth_type=AUTH_TYPE,
            model_id=self.embed_model_name,
            service_endpoint=self.embed_endpoint,
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

    def get_sql_from_cache(self, user_request):
        """
        try to find the request (NL) in the SQL cache
        """
        cached_result = self.request_cache.get_request_with_stats(user_request)
        if cached_result:
            if len(cached_result["sql"]) > 0:
                self.logger.info("")
                self.logger.info("Found request in cache...")
                return cached_result["sql"]
        # if not found return None
        return None

    def generate_sql_query(self, user_request, user_group_id=None):
        """
        Generate the SQL query based on the user request and restricted schema.

        Args:
            user_request (str): The user’s SQL query request.

        Returns:
            str: The generated SQL query.
        """
        # if the request is found in cache return it
        sql_in_cache = self.get_sql_from_cache(user_request)

        if sql_in_cache is not None:
            # return immediately
            return sql_in_cache

        # generate
        time_start = time.time()
        restricted_schema = self.generate_restricted_schema(user_request)

        self.logger.info("Generating SQL query...")

        sql_query = self._generate_sql_with_models(
            user_request,
            restricted_schema,
            self.prompt_template,
            user_group_id,
        )
        time_elapsed = round(time.time() - time_start, 1)

        if len(sql_query) > 0:
            # ok, generated
            self.logger.info(
                "SQL query generated, elapsed time: %3.1f sec.", time_elapsed
            )
            success = True
        else:
            # query not generated
            success = False

        self.request_cache.add_to_cache(
            user_request, sql_query, success=success, generation_time=time_elapsed
        )
        return sql_query

    #
    # Helper
    #
    def _generate_sql_with_models(
        self,
        user_query,
        schema,
        prompt_template,
        user_group_id=None,
    ):
        """
        Combine SQL generation and post-processing.
        Use the list of models... if with the first get error then try with second
        and so on until one succeed
        Args:
            user_query (str): User-provided query.
            schema (str): Formatted schema information.
            engine: used to test the sintax of the generated query
            llm_list: Language model list
        Returns:
            str: Cleaned SQL query, empty if wrong
        """
        for llm in self.llm_manager.llm_models:
            sql_query, _ = self.llm_manager.generate_sql(
                user_query, schema, llm, prompt_template, user_group_id
            )

            if sql_query:
                cleaned_query = clean_sql_query(sql_query)
                if self.db_manager.test_query_syntax(cleaned_query):
                    return cleaned_query  # Return on first success

            # if here the previous showed errors
            self.logger.info("Trying with another model...")

        self.logger.error("All models failed to generate a valid SQL query.")
        self.logger.info("User query: %s", user_query)

        # return empty ig generation doesn't succeed
        return ""
