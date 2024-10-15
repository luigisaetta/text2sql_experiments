"""
AI DataAnalyzer

the component, based on LLM, used to create reports based on Data

It is also used to generate an answer when the request is not understood
by the router
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
Base your answers strictly on the question, the provided information 
and prior messages in the conversation.
"""

# this are preamble and template used for chat with your data
PREAMBLE_U = """You are an AI assistant.
Your task is to answer to requests 
by referencing the conversation history.
Base your answers strictly on the question, the provided information 
and prior messages in the conversation.
If the request is not clear, make the appropriate questions to clarify.
"""

# preamble is passed as a system message
analyze_template = ChatPromptTemplate.from_messages(
    [("system", PREAMBLE), MessagesPlaceholder("msgs")]
)

clarify_template = ChatPromptTemplate.from_messages(
    [("system", PREAMBLE_U), MessagesPlaceholder("msgs")]
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
        return analyze_chain.invoke({"msgs": msgs})

    def answer_not_defined(self, msgs):
        """
        To handle a request not classified by the router
        """

        # build the chain
        llm_c = self.llm_manager.llm_models[INDEX_MODEL_FOR_EXPLANATION]
        clarify_chain = clarify_template | llm_c

        # msgs[-1] is the last request
        return clarify_chain.invoke({"msgs": msgs})
