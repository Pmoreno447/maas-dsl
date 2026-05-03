# agents.py
from langchain_core.messages import SystemMessage, HumanMessage
from prompt import AGENTE1, AGENTE2
from state import State
from langchain.chat_models import init_chat_model
from langgraph.config import get_stream_writer





# Salidas de los nodos


# Modelos
modelAgent1 = init_chat_model(model="openai:gpt-4o-mini", temperature=0)
modelAgent2 = init_chat_model(model="openai:gpt-4o-mini", temperature=0)



# Nodos del grafo
def nodeAgent1(state: State):
    """"""
    get_stream_writer()({"status": " 🖥️ programando funcion..."})
    result = modelAgent1.invoke(
        [SystemMessage(content=AGENTE1)]
        + state["messages"]
        
    )
    return {"messages": [result]}

def nodeAgent2(state: State):
    """"""
    get_stream_writer()({"status": " ✍🏼 revisando funcion..."})
    result = modelAgent2.invoke(
        [SystemMessage(content=AGENTE2)]
        + state["messages"]
        
    )
    return {"messages": [result]}
