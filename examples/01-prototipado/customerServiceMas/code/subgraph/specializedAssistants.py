from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from typing import Literal, TypedDict
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.chat_models import init_chat_model
from state import State
from prompt import PROBLEMORCHESTRATOR
from agents import nodeShippingHelper, nodePaymentHelper, nodeProductHelper, nodeGeneralHelper


COORDINADOR_ENRUTAMIENTO = """
Debes responder siempre con un objeto JSON con un único campo "next".
Los valores válidos para "next" son:
- "shippinghelper"
- "paymenthelper"
- "producthelper"
- "generalhelper"
- "FINISH"

Reglas:
- Delega al agente más adecuado para gestionar la solicitud.
- Delega a UN SOLO especialista por turno.
- El bloque "Estado actual del sistema" muestra los campos del estado compartido que los especialistas escriben tras actuar; úsalos para saber si una tarea ya está resuelta y, en ese caso, responde "FINISH".
- No delegues al mismo agente dos veces para la misma solicitud.

"""

class Router(TypedDict):
    next: Literal["shippinghelper", "paymenthelper", "producthelper", "generalhelper", "FINISH"]

modelCoordinator = init_chat_model(model="openai:gpt-5-nano", temperature=0)

def coordinator_node(state: State) -> Command[Literal["shippinghelper", "paymenthelper", "producthelper", "generalhelper", "__end__"]]:
    messages = (
        [SystemMessage(content=COORDINADOR_ENRUTAMIENTO + PROBLEMORCHESTRATOR)]
        + state["messages"]
        + [HumanMessage(content=f"""
Estado actual del sistema:
        - decision (Decisión tomada para resolver el pedido): {state.get("decision", "No registrado aún")}
    """)]
    )
    response = modelCoordinator.with_structured_output(Router).invoke(messages)
    goto = END if response["next"] == "FINISH" else response["next"]
    return Command(goto=goto)

def build_specializedAssistants():
    builder = StateGraph(State)

    builder.add_node("coordinator", coordinator_node)
    builder.add_node("shippinghelper", nodeShippingHelper)
    builder.add_node("paymenthelper", nodePaymentHelper)
    builder.add_node("producthelper", nodeProductHelper)
    builder.add_node("generalhelper", nodeGeneralHelper)

    builder.add_edge(START, "coordinator")
    builder.add_edge("shippinghelper", "coordinator")
    builder.add_edge("paymenthelper", "coordinator")
    builder.add_edge("producthelper", "coordinator")
    builder.add_edge("generalhelper", "coordinator")

    return builder.compile()
