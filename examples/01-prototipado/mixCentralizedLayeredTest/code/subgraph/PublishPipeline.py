from langgraph.graph import StateGraph, START, END
from state import State
from agents import nodeFormatter, nodeValidator, nodePublisher

def build_PublishPipeline():
    builder = StateGraph(State)

    builder.add_node("formatter", nodeFormatter)
    builder.add_node("validator", nodeValidator)
    builder.add_node("publisher", nodePublisher)

    builder.add_edge(START, "formatter")
    builder.add_edge("formatter", "validator")
    builder.add_edge("validator", "publisher")
    builder.add_edge("publisher", END)

    return builder.compile()
