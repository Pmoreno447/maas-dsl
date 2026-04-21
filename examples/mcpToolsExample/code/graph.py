from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from state import State
import os
from config import OPENAI_API_KEY

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

from agents import nodeSearcher, nodeFormatter, nodeResponder

# Construcción del grafo
builder = StateGraph(State)

# Nodos
builder.add_node("searcher", nodeSearcher)
builder.add_node("formatter", nodeFormatter)
builder.add_node("responder", nodeResponder)

# Edges
builder.add_edge(START, "searcher")
builder.add_edge("searcher", "formatter")
builder.add_edge("formatter", "responder")
builder.add_edge("responder", END)

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

# Ejecucion (Provisional, solo para probar en las primeras iteraciones del generador)
import asyncio

async def main():
    entrada = """
    Investiga sobre que es langgraph
"""
    result = await graph.ainvoke({
        "messages": [HumanMessage(content=entrada)]
    })
    print_state(result)

asyncio.run(main())
