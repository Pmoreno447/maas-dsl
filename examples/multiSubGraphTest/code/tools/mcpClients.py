# tools/mcpClients.py — ARCHIVO GENERADO AUTOMÁTICAMENTE — NO EDITAR A MANO
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from config import TAVILY_API_KEY

_client = MultiServerMCPClient({
    "Tavily": {
        "url": "https://mcp.tavily.com/mcp/?tavilyApiKey={key}".replace("{key}", TAVILY_API_KEY),
        "transport": "streamable_http",
    },
})

_all_tools = asyncio.run(_client.get_tools())

def _get_tool(name: str):
    tool = next((t for t in _all_tools if t.name == name), None)
    if tool is None:
        raise RuntimeError(f"Tool '{name}' no encontrada en el servidor MCP. Tools disponibles: {[t.name for t in _all_tools]}")
    return tool

tavily_search =  _get_tool("tavily_search")
tavily_extract =  _get_tool("tavily_extract")
