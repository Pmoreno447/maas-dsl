from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from state import State
import os
from config import OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

from agents import nodeResearcher, nodeWriter, nodeCritic, nodeEditor

# Construcción del grafo
builder = StateGraph(State)

# Nodos
builder.add_node("researcher", nodeResearcher)
builder.add_node("writer", nodeWriter)
builder.add_node("critic", nodeCritic)
builder.add_node("editor", nodeEditor)

# Edges
builder.add_edge(START, "researcher")
builder.add_edge("researcher", "writer")
builder.add_edge("writer", "critic")
builder.add_edge("critic", "editor")
builder.add_edge("editor", END)

# Compilar
graph = builder.compile()

# Ejecucion (Provisional, solo para probar en las primeras iteraciones del generador)
entrada = """
    # Rellenar
"""

result = graph.invoke({
    "messages": [HumanMessage(content=entrada)]
})

def print_state(result: dict):
    print("💬 MENSAJES:")
    for i, msg in enumerate(result.get("messages", [])):
        content = msg.content if hasattr(msg, "content") else str(msg)
        print(f"  [{i}] {type(msg).__name__}: {content}")

    print("📦 ESTADO:")
    for key, value in result.items():
        if key != "messages":
            print(f"  {key}: {value}")

print_state(result)
