"""
Router
"""

import json
from langchain_core.prompts import PromptTemplate
from llm_manager import LLMManager
from prompt_routing import PROMPT_ROUTING
from utils import get_console_logger

from config import INDEX_MODEL_FOR_ROUTING, DEBUG


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

    def extract_json(self, text):
        """
        extract from the content the portion between {} (included)
        """
        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1:
            # {} are included
            result = text[start : end + 1]
        else:
            result = "{}"

        return result

    def classify(self, user_request: str) -> str:
        """
        classify in one of this categories:
            generate_sql
            analyze_text
            ...
        """
        logger = get_console_logger()

        classify_prompt = PromptTemplate.from_template(PROMPT_ROUTING)
        llm_c = self.llm_manager.llm_models[INDEX_MODEL_FOR_ROUTING]
        classify_chain = classify_prompt | llm_c

        # invoke the LLM
        result = classify_chain.invoke({"question": user_request})

        if DEBUG:
            logger.info("Router:classify: %s", result)

        # json in the format {"classification": value}
        json_string = self.extract_json(result.content)

        # convert in dict
        data = json.loads(json_string)

        classification_value = data["classification"]

        return classification_value
