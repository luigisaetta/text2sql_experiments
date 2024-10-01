"""
Router
"""

from langchain_core.prompts import PromptTemplate
from llm_manager import LLMManager
from prompt_template import PROMPT_ROUTING
from utils import get_console_logger

from config import INDEX_MODEL_FOR_ROUTING, DEBUG


class Router:
    """
    Wraps all the code needed to use the decide
    what is the type of user request
    """

    def __init__(self, llm_manager: LLMManager):
        """ "
        init
        """
        self.llm_manager = llm_manager

    def extract_json(self, text):
        """
        extract frok the content the portion between {} (included)
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
        classify in one of two categories:
            generate_sql
            analyze_text
        """
        logger = get_console_logger()

        classify_prompt = PromptTemplate.from_template(PROMPT_ROUTING)

        llm_c = self.llm_manager.llm_models[INDEX_MODEL_FOR_ROUTING]
        classify_chain = classify_prompt | llm_c

        result = classify_chain.invoke({"question": user_request})

        if DEBUG:
            logger.info("Router:classify: %s", result)

        # json in the format {"classification": value}
        return self.extract_json(result.content)
