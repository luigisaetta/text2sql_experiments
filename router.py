"""
File name: router.py
Author: Luigi Saetta
Date last modified: 2024-10-21
Python Version: 3.11

Description:
    This file provide a class to handle the routing of user requests
    This class provides the logic (based on LLM) to identify a request 
    and route for right action

Inspired by:
   

Usage:
    Import this module into other scripts to use its functions. 
    Example:


License:
    This code is released under the MIT License.

Notes:
    This is a part of a set of demos showing how to build a SQL Agent
    for Text2SQL taks

Warnings:
    This module is in development, may change in future versions.
"""

from langchain_core.prompts import PromptTemplate
from llm_manager import LLMManager
from prompt_routing import PROMPT_ROUTING
from utils import get_console_logger

from config import INDEX_MODEL_FOR_ROUTING, DEBUG

# the list of string used as labels
# (15/10) not allowed introduced to protect from DDL and DML
ALLOWED_VALUES = ["generate_sql", "analyze_data", "not_defined", "not_allowed"]

# this is the JSON schema for the output
json_schema = {
    "title": "classification",
    "description": "the classification of the request.",
    "type": "object",
    "properties": {
        "classification": {
            "type": "string",
            # allowed values
            "enum": ALLOWED_VALUES,
            "description": "the class of the request",
        },
    },
    "required": ["classification"],
}


class Router:
    """
    Wraps all the code needed to decide
    what is the type of user request
    """

    def __init__(self, llm_manager: LLMManager):
        """ "
        init
        """
        self.llm_manager = llm_manager
        self.logger = get_console_logger()

    def classify(self, user_request: str) -> str:
        """
        classify in one of this categories:
            generate_sql
            analyze_text
            ...
        """
        # define the prompt to be used with few shot examples
        classify_prompt = PromptTemplate.from_template(PROMPT_ROUTING)
        # get llm to be used
        llm_c = self.llm_manager.llm_models[
            INDEX_MODEL_FOR_ROUTING
        ].with_structured_output(json_schema)
        # the chain
        classify_chain = classify_prompt | llm_c

        # invoke the LLM, output is a dict
        try:
            result = classify_chain.invoke({"question": user_request})

            if DEBUG:
                self.logger.info("Router:classify: %s", result)

            classification_value = result["classification"]
        except Exception as e:
            self.logger.error("Error in Router:classify %s", e)
            classification_value = None

        return classification_value
