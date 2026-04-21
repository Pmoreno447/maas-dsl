# agents.py
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from prompt import SEARCHER, FORMATTER, RESPONDER
from state import State
from langchain.chat_models import init_chat_model


from tools.mcpClients import tavily_search, tavily_extract
from tools.prueba import prueba

# Salidas de los nodos


# Modelos
modelSearcher = init_chat_model(model="openai:gpt-4o-mini", temperature=0).bind_tools([tavily_search, tavily_extract])
modelFormatter = init_chat_model(model="openai:gpt-4o-mini", temperature=0).bind_tools([prueba])
modelResponder = init_chat_model(model="openai:gpt-4o-mini", temperature=0)

_tools_by_name = {t.name: t for t in [tavily_search, tavily_extract, prueba]}

# Nodos del grafo
async def nodeSearcher(state: State):
    """"""
    messages = (
        [SystemMessage(content=SEARCHER)]
        + state["messages"]
        
    )
    while True:
        response = await modelSearcher.ainvoke(messages)
        messages.append(response)
        if not response.tool_calls:
            return {"messages": [response]}
        for tc in response.tool_calls:
            tool = _tools_by_name[tc["name"]]
            try:
                result = await tool.ainvoke(tc["args"])
                messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
            except Exception as e:
                messages.append(ToolMessage(content=f"Error al llamar herramienta '{tc['name']}': {e}", tool_call_id=tc["id"]))

async def nodeFormatter(state: State):
    """"""
    messages = (
        [SystemMessage(content=FORMATTER)]
        + state["messages"]
        
    )
    while True:
        response = await modelFormatter.ainvoke(messages)
        messages.append(response)
        if not response.tool_calls:
            return {"messages": [response]}
        for tc in response.tool_calls:
            tool = _tools_by_name[tc["name"]]
            try:
                result = await tool.ainvoke(tc["args"])
                messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
            except Exception as e:
                messages.append(ToolMessage(content=f"Error al llamar herramienta '{tc['name']}': {e}", tool_call_id=tc["id"]))

def nodeResponder(state: State):
    """"""
    result = modelResponder.invoke(
        [SystemMessage(content=RESPONDER)]
        + state["messages"]
        
    )
    return {"messages": [result]}
