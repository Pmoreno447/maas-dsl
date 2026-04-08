import os
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from prompt import ORGANIZADOR, INVESTIGADOR, REDACTOR, VALIDADOR
from state import State

# Structured output para el organizador
class Decision(BaseModel):
    next: str = Field(description="Siguiente agente", enum=["investigador", "redactor", "validador", "final"])
    reason: str = Field(description="Razón de la decisión")

_tavily_key = os.getenv('TAVILY_API_KEY')
if not _tavily_key:
    raise ValueError("TAVILY_API_KEY no está definida en las variables de entorno")

mcp_client = MultiServerMCPClient({
    "tavily": {
        "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={_tavily_key}",
        "transport": "streamable_http",
    }
})

# Modelos (el investigador se bindea con tools dentro de la sesión)
mcp_tools = []
modeloOrganizador = init_chat_model(model="openai:gpt-5-nano", temperature=0).with_structured_output(Decision)
modeloInvestigador = init_chat_model(model="openai:gpt-5-nano", temperature=0)
modeloRedactor = init_chat_model(model="openai:gpt-5-nano", temperature=0)
modeloRevisor = init_chat_model(model="openai:gpt-5-nano", temperature=0)

async def init():
    global mcp_tools, modeloInvestigador
    mcp_tools = await mcp_client.get_tools()
    modeloInvestigador = modeloInvestigador.bind_tools(mcp_tools)

# Nodos del grafo
def nodoOrganizador(state):
    """Decide a qué agente enviar el trabajo"""
    decision = modeloOrganizador.invoke(
        [SystemMessage(content=ORGANIZADOR)]
        + state["messages"]
    )
    return {"next": decision.next}

async def nodoInvestigador(state):
    """Busca artículos en internet usando Tavily"""
    messages = [SystemMessage(content=INVESTIGADOR)] + state["messages"]

    while True:
        response = await modeloInvestigador.ainvoke(messages)
        messages.append(response)

        if not response.tool_calls:
            break

        for tc in response.tool_calls:
            tool = next(t for t in mcp_tools if t.name == tc["name"])
            result = await tool.ainvoke(tc["args"])
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    return {"messages": [response]}

def nodoRedactor(state):
    """Redacta el paper"""
    return {
        "messages": [
            modeloRedactor.invoke(
                [SystemMessage(content=REDACTOR)]
                + state["messages"]
            )
        ]
    }

def nodoRevisor(state):
    """Revisa el paper"""
    return {
        "messages": [
            modeloRevisor.invoke(
                [SystemMessage(content=VALIDADOR)]
                + state["messages"]
            )
        ]
    }