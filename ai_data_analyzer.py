"""
AI DataAnalyzer

the componen, based on LLM, used to create reports based on Data
"""

from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)

from llm_manager import LLMManager

from config import INDEX_MODEL_FOR_EXPLANATION
from utils import get_console_logger

# this are preamble and template used for chat with your data
PREAMBLE = """You are an AI assistant.
Your task is to explain the provided data and respond to requests 
by referencing both the given data and the conversation history.
Base your answers strictly on the provided information and prior messages in the conversation.
"""

analyze_template = ChatPromptTemplate.from_messages(
    [("system", PREAMBLE), MessagesPlaceholder("msgs")]
)


class AIDataAnalyzer:
    """
    Wraps all the code needed to analyze data
    """

    def __init__(self, llm_manager: LLMManager):
        """ "
        init
        """
        self.llm_manager = llm_manager
        self.logger = get_console_logger()

        self.logger.info("Initialised Data Analyzer...")

    def analyze(self, msgs):
        """
        Analyze the data

        msgs: the msgs history
        user request is msgs[-1]
        """
        # build the chain
        llm_c = self.llm_manager.llm_models[INDEX_MODEL_FOR_EXPLANATION]
        analyze_chain = analyze_template | llm_c

        # msgs[-1] is the last request
        ai_message = analyze_chain.invoke({"msgs": msgs})

        return ai_message
