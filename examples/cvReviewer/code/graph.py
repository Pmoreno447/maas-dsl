# graph.py
import asyncio
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from state import State
from agents import nodoExtractor, nodoEvaluator, nodoReportGenerator, nodoNotifier


# Construcción del grafo
builder = StateGraph(State)

# Nodos
builder.add_node("extractor", nodoExtractor)
builder.add_node("evaluator", nodoEvaluator)
builder.add_node("reportGenerator", nodoReportGenerator)
builder.add_node("notifier", nodoNotifier)

# Edges (pipeline lineal)
builder.add_edge(START, "extractor")
builder.add_edge("extractor", "evaluator")
builder.add_edge("evaluator", "reportGenerator")
builder.add_edge("reportGenerator", "notifier")
builder.add_edge("notifier", END)

# Compilar
graph = builder.compile()


# Ejecución
async def main():
    cv_text = """
    Nombre: Juan García
    Email: juan.garcia@email.com
    Experiencia: 5 años como desarrollador backend en Python y Java.
    Estudios: Grado en Ingeniería Informática
    Idiomas: Español nativo, Inglés B2
    Habilidades: Python, Java, Docker, Kubernetes, PostgreSQL
    """

    result = await graph.ainvoke({
        "messages": [HumanMessage(content=cv_text)]
    })

    print("\n📋 INFORME FINAL:")
    print(result["reportText"])
    print(f"\n✅ Recomendación: {result['recommendation']}")


if __name__ == "__main__":
    asyncio.run(main())