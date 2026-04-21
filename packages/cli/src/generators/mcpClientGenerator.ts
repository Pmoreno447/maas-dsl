import type { LLMMultiAgentSystem, MCPServer } from 'multi-agent-dsl-language';
import { isMCPServer } from 'multi-agent-dsl-language';
import { expandToNode, joinToNode, toString } from 'langium/generate';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { extractDestinationAndName, collectMcpApiKeyEnvVars } from '../util.js';

// Construye la expresión Python que evalúa a la URL final del server MCP.
// Si el server declara `apiKeyName`, emite un `.replace("{key}", <VAR>)` para
// que la env var importada de `config.py` sustituya el placeholder. Si no,
// devuelve la URL cruda — cubre servers sin auth sin introducir replace
// innecesario.
function serverUrlPythonExpr(server: MCPServer): string {
    return server.apiKeyName
        ? `"${server.url}".replace("{key}", ${server.apiKeyName})`
        : `"${server.url}"`;
}

// ─── Generator ────────────────────────────────────────────────────────────────
export function mcpClientGenerator(model: LLMMultiAgentSystem, filePath: string, destination: string | undefined): string | null {
    const servers = model.tools.filter(isMCPServer);
    if (servers.length === 0) return null;

    const data = extractDestinationAndName(filePath, destination);
    const toolsDir = path.join(data.destination, 'tools');
    const generatedFilePath = path.join(toolsDir, 'mcpClients.py');

    const apiKeys = collectMcpApiKeyEnvVars(model.tools);
    const importLine = apiKeys.length > 0
        ? `from config import ${apiKeys.join(', ')}`
        : '';

    const serverEntries = joinToNode(servers, server =>
`    "${server.name}": {
        "url": ${serverUrlPythonExpr(server)},
        "transport": "${server.transport}",
    },`
    , { appendNewLineIfNotEmpty: true });

    const toolVariables = joinToNode(
        servers.flatMap(s => s.tools),
        toolName => `${toolName} =  _get_tool("${toolName}")`,
        { appendNewLineIfNotEmpty: true }
    );

    const fileNode = expandToNode`
# tools/mcpClients.py — ARCHIVO GENERADO AUTOMÁTICAMENTE — NO EDITAR A MANO
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
${importLine}

_client = MultiServerMCPClient({
${serverEntries}})

_all_tools = asyncio.run(_client.get_tools())

def _get_tool(name: str):
    tool = next((t for t in _all_tools if t.name == name), None)
    if tool is None:
        raise RuntimeError(f"Tool '{name}' no encontrada en el servidor MCP. Tools disponibles: {[t.name for t in _all_tools]}")
    return tool

${toolVariables}
`.appendNewLineIfNotEmpty();

    if (!fs.existsSync(toolsDir)) {
        fs.mkdirSync(toolsDir, { recursive: true });
    }
    fs.writeFileSync(generatedFilePath, toString(fileNode));
    return generatedFilePath;
}
