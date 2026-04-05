# main.py
import asyncio
from langgraph.graph import StateGraph, END
from state import State
from agents import (
    nodoOrganizador,
    nodoInvestigador,
    nodoRedactor,
    nodoRevisor,
    init
)

def router(state):
    return state["next"]

async def main():
    await init()

    g = StateGraph(State)

    g.add_node("organizador", nodoOrganizador)
    g.add_node("investigador", nodoInvestigador)
    g.add_node("redactor", nodoRedactor)
    g.add_node("revisor", nodoRevisor)

    g.set_entry_point("organizador")

    g.add_conditional_edges("organizador", router, {
        "investigador": "investigador",
        "redactor": "redactor",
        "validador": "revisor",
        "final": END,
    })

    g.add_edge("investigador", "organizador")
    g.add_edge("redactor", "organizador")
    g.add_edge("revisor", "organizador")

    app = g.compile()

    async for event in app.astream({
        "messages": [("user", "Quiero un documento sobre qué es Quarkus el framework de Java")]
    }):
        for node_name, output in event.items():
            print(f"\n{'='*50}")
            print(f"NODO: {node_name}")
            print(f"{'='*50}")
            if "messages" in output:
                print(output["messages"][-1].content[:300])
            if "next" in output:
                print(f"-> Siguiente: {output['next']}")

asyncio.run(main())