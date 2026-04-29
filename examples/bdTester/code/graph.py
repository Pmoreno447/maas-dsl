import os
from config import OPENAI_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from state import State
from subgraph.example import build_example



# Construcción del grafo
builder = StateGraph(State)

# Subgrafos como nodos
example = build_example()

builder.add_node("example", example)

# Edges de inicio
builder.add_edge(START, "example")

# Routers


# Transiciones
builder.add_edge("example", END)

# Compilar
graph = builder.compile()
