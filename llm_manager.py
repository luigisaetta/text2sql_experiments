"""
LLMManager
"""

from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain.prompts import PromptTemplate

from core_functions import extract_sql_from_response


class LLMManager:
    """
    The class handle all the LLM-related tasks
    """

    def __init__(self, model_list, endpoint, compartment_id, temperature, logger):
        self.model_list = model_list
        self.endpoint = endpoint
        self.compartment_id = compartment_id
        self.temperature = temperature
        self.logger = logger
        self.llm_models = self.initialize_models()

    def initialize_models(self):
        """
        Initialise the list of ChatModels to be used to generate SQL
        """
        models = []
        for model in self.model_list:
            models.append(
                ChatOCIGenAI(
                    model_id=model,
                    service_endpoint=self.endpoint,
                    compartment_id=self.compartment_id,
                    model_kwargs={"temperature": self.temperature, "max_tokens": 2048},
                )
            )
        return models

    def generate_sql(self, user_query, schema, llm, prompt_template):
        """
        generate the SQL for a user request
        """
        try:
            prompt = PromptTemplate(
                template=prompt_template, input_variables=["schema", "query"]
            )
            llm_chain = prompt | llm

            response = llm_chain.invoke({"schema": schema, "query": user_query})

            sql_query = extract_sql_from_response(response.content)

            return sql_query, response.content
        except Exception as e:
            self.logger.error("Error generating SQL: %s", e)
            return None, None
