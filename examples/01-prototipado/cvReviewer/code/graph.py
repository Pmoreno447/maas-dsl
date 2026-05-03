import os
from config import OPENAI_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from state import State, should_summarize, summary_node
from subgraph.Grafo import build_Grafo



# Construcción del grafo
builder = StateGraph(State)

# Subgrafos como nodos
Grafo = build_Grafo()

builder.add_node("grafo", Grafo)

builder.add_node("summary_node", summary_node)
builder.add_edge("summary_node", END)

# Edges de inicio
builder.add_edge(START, "grafo")

# Routers


# Transiciones
builder.add_conditional_edges(
    "grafo",
    should_summarize,
    {
        "summary_node": "summary_node",
        END: END
    }
)

# Compilar
graph = builder.compile()
