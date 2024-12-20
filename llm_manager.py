"""
File name: llm_manager.py
Author: Luigi Saetta
Date last modified: 2024-10-21
Python Version: 3.11

Description:
    Encapsulate the managemnt of LLM models

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
    for Text2SQL tasks

Warnings:
    This module is in development, may change in future versions.
"""

from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain.prompts import PromptTemplate

from core_functions import extract_sql_from_response
from config import AUTH_TYPE, MAX_TOKENS


class LLMManager:
    """
    The class handle all the LLM-related tasks
    """

    def __init__(
        self, model_list, model_endpoints, compartment_id, temperature, logger
    ):
        self.model_list = model_list
        self.model_endpoints = model_endpoints
        self.compartment_id = compartment_id
        self.temperature = temperature
        self.logger = logger
        self.llm_models = self.initialize_models()

    def initialize_models(self):
        """
        Initialise the list of ChatModels to be used to generate SQL
        """
        self.logger.info("LLMManager: Initialising the list of models...")

        models = []
        for model, endpoint in zip(self.model_list, self.model_endpoints):
            self.logger.info("Model: %s", model)

            models.append(
                ChatOCIGenAI(
                    # modified to support no-default auth (inst_princ..)
                    auth_type=AUTH_TYPE,
                    model_id=model,
                    service_endpoint=endpoint,
                    compartment_id=self.compartment_id,
                    model_kwargs={
                        "temperature": self.temperature,
                        "max_tokens": MAX_TOKENS,
                    },
                )
            )
        return models

    def get_llm_models(self):
        """
        return the list of initialised models
        """
        return self.llm_models

    def generate_sql(
        self, user_query, schema, llm, prompt_template, user_group_id=None
    ):
        """
        generate the SQL for a user request

        user_group_id: integer identifying the group the user belongs to
        to enable RBAC
        """
        try:
            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=["schema", "query", "user_group_id"],
            )
            llm_chain = prompt | llm

            # added user_group_id for RBAC. Can be None
            response = llm_chain.invoke(
                {"schema": schema, "query": user_query, "user_group_id": user_group_id}
            )

            sql_query = extract_sql_from_response(response.content)

            return sql_query, response.content
        except Exception as e:
            self.logger.error("Error generating SQL: %s", e)
            return None, None
