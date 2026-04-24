from langgraph.graph import StateGraph, START, END
from state import State
from agents import nodeSearcher, nodeFormatter, nodeResponder

def build_Pipeline2():
    builder = StateGraph(State)

    builder.add_node("searcher", nodeSearcher)
    builder.add_node("formatter", nodeFormatter)
    builder.add_node("responder", nodeResponder)

    builder.add_edge(START, "searcher")
    builder.add_edge("searcher", "formatter")
    builder.add_edge("formatter", "responder")
    builder.add_edge("responder", END)

    return builder.compile()
