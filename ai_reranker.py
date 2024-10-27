"""
File name: ai_reranker
Author: Luigi Saetta
Date last modified: 2024-10-27
Python Version: 3.11

Description:
    Encapsulate the code for reranking

    in this way all the code needed for reranking is in a single class
    - I have added reranking to RAG, after vector search

Inspired by:
   
Usage:
    Import this module into other scripts to use its functions. 
    Example:

Dependencies:
    LangChain

License:
    This code is released under the MIT License.

Notes:
    This is a part of a set of demos showing how to build a SQL Agent
    for Text2SQL taks

Warnings:
    This module is in development, may change in future versions.
"""

import re
from langchain_core.prompts import PromptTemplate

from prompt_template import PROMPT_RERANK_TABLES

from config import TOP_N, INDEX_MODEL_FOR_RERANKING

RERANK_DOCS_PROMPT = """
Rank the following documents by their relevance to the question:
Question: {question}
Documents:
{documents}

Order the documents in the format: 
1. <most relevant document>, 
2. <second most relevant>, etc.

List only the indexes of the documents in the format:
1. Document x
2. Document z

Do not add any other comment, provide only the list.
Remove only documents strictly not relevant to the question.
Enclose always the list in triple backticks.

"""


class Reranker:
    """
    In this class we encapsulate all the code where we use an LLM for reranking
    """

    def __init__(self, llm_manager, logger):
        """
        Initializes the Reranker.

        llm_manager: Manages the LLM models.
        logger: Logger instance.
        """
        self.llm_manager = llm_manager
        self.logger = logger

    def rerank_table_list(self, query, top_k_schemas):
        """
        query: the user query in NL
        top_k_schemas: schemas returned from similarity search
        """
        table_select_prompt = PromptTemplate.from_template(PROMPT_RERANK_TABLES)

        llm_r = self.llm_manager.llm_models[INDEX_MODEL_FOR_RERANKING]
        rerank_chain = table_select_prompt | llm_r

        result = rerank_chain.invoke(
            {
                "top_n": TOP_N,
                "table_schemas": top_k_schemas,
                "question": query,
            }
        )

        return result

    def rerank_docs_for_rag(self, query, docs):
        """
        This is the function used by the RAG Agent
        """
        rerank_docs_prompt = PromptTemplate.from_template(RERANK_DOCS_PROMPT)

        llm_r = self.llm_manager.llm_models[INDEX_MODEL_FOR_RERANKING]
        rerank_chain = rerank_docs_prompt | llm_r
        documents_text = "\n".join(
            f"{i+1}. {doc.page_content}" for i, doc in enumerate(docs)
        )
        rerank_input = {"question": query, "documents": documents_text}

        rerank_result = rerank_chain.invoke(rerank_input)

        self.logger.info("")
        self.logger.info("Reranking results:")

        # extract on the indexes
        indexes = self._extract_docs_indexes(rerank_result.content)

        self.logger.info(indexes)

        # be careful, in the list index start by 0 not i
        # in indexes they start from 1
        extracted_docs = [docs[i - 1] for i in indexes]

        # applied strict reranking with filter
        return extracted_docs

    # helper functions
    def _extract_docs_indexes(self, content):
        """
        thel list is enclosed in triple backticks
        """
        text_enclosed = re.search(r"```(.*?)```", content, re.DOTALL).group(1)

        # Estrai gli indici numerici all'inizio di ogni riga
        indexes = [
            int(match.group(1))
            for match in re.finditer(r"Document (\d+)", text_enclosed)
        ]

        return indexes
