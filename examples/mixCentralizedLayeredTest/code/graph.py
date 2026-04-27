from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from state import State
import os
from subgraph.ContentHub import build_ContentHub
from subgraph.PublishPipeline import build_PublishPipeline
from config import OPENAI_API_KEY

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


# Construcción del grafo
builder = StateGraph(State)

# Subgrafos como nodos
ContentHub = build_ContentHub()
PublishPipeline = build_PublishPipeline()

builder.add_node("contenthub", ContentHub)
builder.add_node("publishpipeline", PublishPipeline)

# Edges de inicio
builder.add_edge(START, "contenthub")

# Routers
def route_publishpipeline(state: State) -> str:
    if state["score"] < 6:
        return "contenthub"
    if state["approved"] == True:
        return END
    return END

# Transiciones
builder.add_edge("contenthub", "publishpipeline")
builder.add_conditional_edges(
    "publishpipeline",
    route_publishpipeline,
    {
        "contenthub": "contenthub",
        END: END
    }
)

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
