"""
AI RAG Agent

This code encapsulate Semantic Search and answer from RAG 
"""

import oracledb
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)
from langchain_community.vectorstores.oraclevs import OracleVS


from oci_cohere_embeddings_utils import OCIGenAIEmbeddingsWithBatch
from llm_manager import LLMManager

from config import (
    AUTH_TYPE,
    CONNECT_ARGS_VECTOR,
    DISTANCE_STRATEGY,
    TOP_K,
    INDEX_MODEL_FOR_EXPLANATION,
)


# the name of the table to contain docs for policies + embeddings
RAG_COLLECTION_NAME = "POLICIES_COLLECTION"

# this are preamble and template used for chat with your data
PREAMBLE = """You are an AI assistant.
Your task is to respond to requests 
by referencing both the given data and the conversation history.
Base your answers strictly on the question, the provided information 
and prior messages in the conversation.
"""
# preamble is passed as a system message
answer_template = ChatPromptTemplate.from_messages(
    [("system", PREAMBLE), MessagesPlaceholder("msgs")]
)


class AIRAGAgent:
    """
    Wraps all the code needed to use the RAG Agent

    """

    def __init__(
        self,
        vector_connect_args,
        model_list,
        model_endpoints,
        compartment_ocid,
        embed_model_name,
        embed_endpoint,
        temperature,
        logger,
    ):
        """
        Init
        """
        self.vector_connect_args = vector_connect_args
        self.model_list = model_list
        self.model_endpoints = model_endpoints
        self.compartment_ocid = compartment_ocid
        self.embed_model_name = embed_model_name
        self.embed_endpoint = embed_endpoint
        self.temperature = temperature
        self.logger = logger

        self.llm_manager = self._initialize_llm_manager()

        logger.info("RAG Agent initialised...")

    def _initialize_llm_manager(self):
        """Initialize the LLMManager with model list, endpoints, and temperature."""
        return LLMManager(
            self.model_list,
            self.model_endpoints,
            self.compartment_ocid,
            self.temperature,
            self.logger,
        )

    def _get_embed_model(self):
        """get the embedding model"""
        return OCIGenAIEmbeddingsWithBatch(
            auth_type=AUTH_TYPE,
            model_id=self.embed_model_name,
            service_endpoint=self.embed_endpoint,
            compartment_id=self.compartment_ocid,
        )

    def get_relevant_docs(self, user_request):
        """ "
        given a user request, get from the collection relevant chunks of doc
        """
        self.logger.info("Searching for relevant documents in Vector Store...")

        embed_model = self._get_embed_model()

        with self._get_vector_db_connection() as conn:
            v_store = OracleVS(
                conn,
                embed_model,
                table_name=RAG_COLLECTION_NAME,
                distance_strategy=DISTANCE_STRATEGY,
            )

            # get TOP_K chunks, this is a list of Document
            results = v_store.similarity_search(user_request, k=TOP_K)

        return results

    #
    # Helper
    #
    def answer(self, user_request):
        """
        return an answer based on the retrieved docs
        """
        msgs = []

        # do semantic search
        docs = self.get_relevant_docs(user_request)

        # load docs retrieved in msgs
        for doc in docs:
            msgs.append(SystemMessage(doc.page_content))

        # build the chain
        llm_c = self.llm_manager.llm_models[INDEX_MODEL_FOR_EXPLANATION]
        answer_chain = answer_template | llm_c

        # msgs[-1] is the last request
        msgs.append(HumanMessage(user_request))

        return answer_chain.invoke({"msgs": msgs})

    def _get_vector_db_connection(self):
        """Return a database connection to the vector store."""
        return oracledb.connect(**CONNECT_ARGS_VECTOR)