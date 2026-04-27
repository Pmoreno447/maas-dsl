from langgraph.graph import StateGraph, START, END
from state import State
from agents import nodeAnswerWriter

def build_answerWriter():
    builder = StateGraph(State)

    builder.add_node("answerwriter", nodeAnswerWriter)

    builder.add_edge(START, "answerwriter")
    builder.add_edge("answerwriter", END)

    return builder.compile()
