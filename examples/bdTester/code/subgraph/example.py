from langgraph.graph import StateGraph, START, END
from state import State
from agents import nodeAgent1, nodeAgent2

def build_example():
    builder = StateGraph(State)

    builder.add_node("agent1", nodeAgent1)
    builder.add_node("agent2", nodeAgent2)

    builder.add_edge(START, "agent1")
    builder.add_edge("agent1", "agent2")
    builder.add_edge("agent2", END)

    return builder.compile()
