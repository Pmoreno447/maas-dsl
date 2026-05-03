from langgraph.graph import StateGraph, START, END
from state import State
from agents import nodeInfoExtractor

def build_ExtractorGraph():
    builder = StateGraph(State)

    builder.add_node("infoextractor", nodeInfoExtractor)

    builder.add_edge(START, "infoextractor")
    builder.add_edge("infoextractor", END)

    return builder.compile()
