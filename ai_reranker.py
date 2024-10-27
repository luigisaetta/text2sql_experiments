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

from langchain_core.prompts import PromptTemplate

from prompt_template import PROMPT_RERANK_TABLES

from config import TOP_N, INDEX_MODEL_FOR_RERANKING


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
        This is the functionused by the RAG Agent
        To be implemented
        """

        # no filter for now
        return docs
