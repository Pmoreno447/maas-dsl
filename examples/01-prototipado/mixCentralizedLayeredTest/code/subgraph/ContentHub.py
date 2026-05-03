from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from typing import Literal, TypedDict
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.chat_models import init_chat_model
from state import State
from prompt import COORDINATOR
from agents import nodeAnalyzer, nodeSummarizer


class Router(TypedDict):
    next: Literal["analyzer", "summarizer", "FINISH"]

modelCoordinator = init_chat_model(model="openai:gpt-4o", temperature=0)

def coordinator_node(state: State) -> Command[Literal["analyzer", "summarizer", "__end__"]]:
    messages = (
        [SystemMessage(content=COORDINATOR)]
        + state["messages"]
        + [HumanMessage(content=f"""
Estado actual del sistema:
        - content (Contenido a procesar): {state["content"]}
        - score (Puntuación de calidad del 0 al 10): {state["score"]}
        - summary (Resumen del contenido generado): {state["summary"]}
    """)]
    )
    response = modelCoordinator.with_structured_output(Router).invoke(messages)
    goto = END if response["next"] == "FINISH" else response["next"]
    return Command(goto=goto)

def build_ContentHub():
    builder = StateGraph(State)

    builder.add_node("coordinator", coordinator_node)
    builder.add_node("analyzer", nodeAnalyzer)
    builder.add_node("summarizer", nodeSummarizer)

    builder.add_edge(START, "coordinator")
    builder.add_edge("analyzer", "coordinator")
    builder.add_edge("summarizer", "coordinator")

    return builder.compile()
