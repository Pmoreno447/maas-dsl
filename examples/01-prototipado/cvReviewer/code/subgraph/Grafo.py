from langgraph.graph import StateGraph, START, END
from state import State
from agents import nodeExtractor, nodeEvaluator, nodeReportGenerator, nodeNotifier

def build_Grafo():
    builder = StateGraph(State)

    builder.add_node("extractor", nodeExtractor)
    builder.add_node("evaluator", nodeEvaluator)
    builder.add_node("reportgenerator", nodeReportGenerator)
    builder.add_node("notifier", nodeNotifier)

    builder.add_edge(START, "extractor")
    builder.add_edge("extractor", "evaluator")
    builder.add_edge("evaluator", "reportgenerator")
    builder.add_edge("reportgenerator", "notifier")
    builder.add_edge("notifier", END)

    return builder.compile()
