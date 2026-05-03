import os
from config import OPENAI_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from state import State
from subgraph.ValidationGraph import build_ValidationGraph
from subgraph.ExtractorGraph import build_ExtractorGraph
from subgraph.answerWriter import build_answerWriter
from subgraph.specializedAssistants import build_specializedAssistants



# Construcción del grafo
builder = StateGraph(State)

# Subgrafos como nodos
ValidationGraph = build_ValidationGraph()
ExtractorGraph = build_ExtractorGraph()
answerWriter = build_answerWriter()
specializedAssistants = build_specializedAssistants()

builder.add_node("validationgraph", ValidationGraph)
builder.add_node("extractorgraph", ExtractorGraph)
builder.add_node("answerwriter", answerWriter)
builder.add_node("specializedassistants", specializedAssistants)

# Edges de inicio
builder.add_edge(START, "validationgraph")

# Routers
def route_validationgraph(state: State) -> str:
    if state["isValid"] == False:
        return "answerwriter"
    if state["isValid"] == True:
        return "extractorgraph"
    return END

# Transiciones
builder.add_conditional_edges(
    "validationgraph",
    route_validationgraph,
    {
        "answerwriter": "answerwriter",
        "extractorgraph": "extractorgraph"
    }
)
builder.add_edge("extractorgraph", "specializedassistants")
builder.add_edge("specializedassistants", "answerwriter")
builder.add_edge("answerwriter", END)

# Compilar
graph = builder.compile()

def print_state(result: dict):
    print("💬 MENSAJES:")
    for i, msg in enumerate(result.get("messages", [])):
        content = msg.content if hasattr(msg, "content") else str(msg)
        print(f"  [{i}] {type(msg).__name__}: {content}")

    print("📦 ESTADO:")
    for key, value in result.items():
        if key != "messages":
            print(f"  {key}: {value}")

# Ejecucion (Provisional)
import asyncio

async def main():
    entrada = """
    # Rellenar
"""
    result = await graph.ainvoke({
        "messages": [HumanMessage(content=entrada)]
    })
    print_state(result)

asyncio.run(main())
