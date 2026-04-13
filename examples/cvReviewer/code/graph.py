from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from state import State
import os
from config import OPENAI_API_KEY

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY # HARDCODEADO EN EL GENERADOR, PROVISIONAL

from agents import nodeExtractor, nodeEvaluator, nodeReportGenerator, nodeNotifier

# Construcción del grafo
builder = StateGraph(State)

# Nodos
builder.add_node("extractor", nodeExtractor)
builder.add_node("evaluator", nodeEvaluator)
builder.add_node("reportgenerator", nodeReportGenerator)
builder.add_node("notifier", nodeNotifier)

# Edges
builder.add_edge(START, "extractor")
builder.add_edge("extractor", "evaluator")
builder.add_edge("evaluator", "reportgenerator")
builder.add_edge("reportgenerator", "notifier")
builder.add_edge("notifier", END)

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
