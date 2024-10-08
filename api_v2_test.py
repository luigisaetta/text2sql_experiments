"""
api_test
"""
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain import LLMChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

from llm_manager import LLMManager
from utils import get_console_logger
from config import API_PORT, API_HOST, MODEL_LIST, MODEL_ENDPOINTS, TEMPERATURE
from config_private import COMPARTMENT_OCID

# Inizializza l'API FastAPI
app = FastAPI()

logger = get_console_logger()

# Creiamo un dizionario per memorizzare solo la memoria di ogni conversazione
conversations = {}

# Definiamo il prompt e l'LLM una sola volta, fuori dalla funzione
prompt_template = PromptTemplate(
    input_variables=["history", "input"],
    template="""
    La conversazione fino ad ora:
    {history}

    Nuova richiesta:
    {input}
    """
)

llm_manager = LLMManager(
    MODEL_LIST, MODEL_ENDPOINTS, COMPARTMENT_OCID, TEMPERATURE, logger
)

llm = llm_manager.llm_models[0]

# Modello per gestire il payload delle richieste
class ConversationRequest(BaseModel):
    conv_id: str  # Identificatore della conversazione
    user_input: str  # Nuova richiesta dell'utente

# Funzione per creare una nuova catena di conversazione usando LCEL con l'operatore `|`
def create_lcel_chain(memory):
    # Usare il prompt e l'LLM per costruire la catena con la memoria configurata
    chain = LLMChain(
        llm=llm,
        prompt=prompt_template,
        memory=memory  # Collega la memoria direttamente qui
    )
    return chain

# Definiamo la route per la conversazione
@app.post("/converse")
async def converse(request: ConversationRequest):
    conv_id = request.conv_id
    user_input = request.user_input

    # Verifica se la memoria per la conversazione esiste già, altrimenti la crea
    if conv_id not in conversations:
        # Crea una nuova memoria per la conversazione
        memory = ConversationBufferMemory()
        conversations[conv_id] = memory
    else:
        # Recupera la memoria esistente
        memory = conversations[conv_id]

    # Crea la catena di conversazione usando il prompt e LLM già configurati
    chain = create_lcel_chain(memory)

    # Genera la risposta usando invoke() invece di predict()
    try:
        response = chain.invoke({"input": user_input})
        return {"conv_id": conv_id, "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#
# Main
#
if __name__ == "__main__":
    uvicorn.run(host=API_HOST, port=API_PORT, app=app)