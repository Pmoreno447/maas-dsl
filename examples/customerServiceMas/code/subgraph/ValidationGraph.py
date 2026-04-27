from langgraph.graph import StateGraph, START, END
from state import State
from agents import nodeValidator

def build_ValidationGraph():
    builder = StateGraph(State)

    builder.add_node("validator", nodeValidator)

    builder.add_edge(START, "validator")
    builder.add_edge("validator", END)

    return builder.compile()
