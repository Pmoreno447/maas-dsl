import type { LLMMultiAgentSystem, Agent } from 'multi-agent-dsl-language';
import { isMCPServer, isPythonTool } from 'multi-agent-dsl-language';
import { expandToNode, toString } from 'langium/generate';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { extractDestinationAndName, toPythonType, toModel, generateNodeName, collectAgentToolNames } from '../util.js';

// ─── Helpers ──────────────────────────────────────────────────────────────────
function isUsingTools(model: LLMMultiAgentSystem): boolean {
    return model.tools.length > 0;
}

function generateStructuredOutput(agent: Agent): string {
    if (!agent.stateUpdate || agent.stateUpdate.length === 0) return '';

    const className = agent.name.charAt(0).toUpperCase() + agent.name.slice(1) + 'Output';
    const fields = agent.stateUpdate.map((ref) =>
        `    ${ref.ref!.name}: ${toPythonType(ref.ref!.type)} = Field(description="${ref.ref!.description}")`
    ).join('\n');

    const toolNames = collectAgentToolNames(agent);
    const hasTools = toolNames.length > 0;
    const docstring = hasTools
        ? `    """Llama a esta herramienta cuando hayas terminado para entregar el resultado final."""\n`
        : '';

    return `class ${className}(BaseModel):\n${docstring}${fields}`;
}

function generateModel(agent: Agent): string {
    const variableName = 'model' + agent.name.charAt(0).toUpperCase() + agent.name.slice(1);
    const className = agent.name.charAt(0).toUpperCase() + agent.name.slice(1) + 'Output';

    const params: string[] = [
        `model="${toModel(agent)}"`,
        `temperature=${agent.temperature ?? 0}`,
    ];
    if (agent.provider === 'ollama') params.push(`base_url=OLLAMA_BASE_URL`);
    if (agent.maxToken)   params.push(`max_tokens=${agent.maxToken}`);
    if (agent.timeOut)    params.push(`timeout=${agent.timeOut}`);
    if (agent.maxRetries) params.push(`max_retries=${agent.maxRetries}`);

    let line = `${variableName} = init_chat_model(${params.join(', ')})`;

    const toolNames = collectAgentToolNames(agent);
    const hasTools = toolNames.length > 0;
    const hasStructured = !!(agent.stateUpdate && agent.stateUpdate.length > 0);

    // BaseModel-as-tool: cuando hay tools y stateUpdate, el schema de salida
    // se bindea como una tool más. El modelo lo invoca cuando ha "terminado"
    // y el while-loop del nodo extrae los args como salida estructurada.
    if (hasTools && hasStructured) {
        line += `.bind_tools([${[...toolNames, className].join(', ')}], tool_choice="required")`;
    } else if (hasTools) {
        line += `.bind_tools([${toolNames.join(', ')}])`;
    } else if (hasStructured) {
        line += `.with_structured_output(${className})`;
    }

    return line;
}

function generateNode(agent: Agent): string {
    const agentPascal = agent.name.charAt(0).toUpperCase() + agent.name.slice(1);
    const nodeName = generateNodeName(agent);
    const modelName = `model${agentPascal}`;
    const profileName = agent.profile.ref!.name.toUpperCase();
    const description = agent.description?.[0] ?? '';
    const className = agentPascal + 'Output';

    const contextFields = agent.stateContext && agent.stateContext.length > 0
        ? `+ [HumanMessage(content=f"""
${agent.stateContext.map(ref => `            ${ref.ref!.name}: {state.get("${ref.ref!.name}", "No registrado aún")}`).join('\n')}
        """)]`
        : '';

    const toolNames = collectAgentToolNames(agent);
    const hasTools = toolNames.length > 0;
    const hasStructured = !!(agent.stateUpdate && agent.stateUpdate.length > 0);

    // Rama sin tools: patrón síncrono clásico.
    if (!hasTools) {
        const returnBlock = hasStructured
            ? `return {\n${agent.stateUpdate!.map(ref =>
                `        "${ref.ref!.name}": result.${ref.ref!.name}`
              ).join(',\n')}\n    }`
            : `return {"messages": [result]}`;

        return `def ${nodeName}(state: State):
    """${description}"""
    result = ${modelName}.invoke(
        [SystemMessage(content=${profileName})]
        + state["messages"]
        ${contextFields}
    )
    ${returnBlock}`;
    }

    // Rama con tools: async + while-loop.
    // Si además hay stateUpdate, el schema (ClassOutput) se bindea como tool
    // terminal: cuando el modelo la invoca, extraemos args como salida estructurada.
    const terminalBlock = hasStructured
        ? `        for tc in response.tool_calls:
            if tc["name"] == "${className}":
                return {\n${agent.stateUpdate!.map(ref =>
                    `                    "${ref.ref!.name}": tc["args"]["${ref.ref!.name}"]`
                  ).join(',\n')}\n                }
`
        : '';

    return `async def ${nodeName}(state: State):
    """${description}"""
    messages = (
        [SystemMessage(content=${profileName})]
        + state["messages"]
        ${contextFields}
    )
    while True:
        response = await ${modelName}.ainvoke(messages)
        messages.append(response)
        if not response.tool_calls:
            return {"messages": [response]}
${terminalBlock}        for tc in response.tool_calls:
            tool = _tools_by_name[tc["name"]]
            try:
                result = await tool.ainvoke(tc["args"])
                messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
            except Exception as e:
                messages.append(ToolMessage(content=f"Error al llamar herramienta '{tc['name']}': {e}", tool_call_id=tc["id"]))`;
}

// ─── Generator ────────────────────────────────────────────────────────────────
export function agentsGenerator(model: LLMMultiAgentSystem, filePath: string, destination: string | undefined): string {
    const data = extractDestinationAndName(filePath, destination);
    const generatedFilePath = `${path.join(data.destination, 'agents')}.py`;

    const messageImports = isUsingTools(model)
        ? 'from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage'
        : 'from langchain_core.messages import SystemMessage, HumanMessage';

    const hasStructuredOutputs = model.agents.some(
        agent => agent.stateUpdate && agent.stateUpdate.length > 0
    );

    const usesOllama = model.agents.some(agent => agent.provider === 'ollama');

    const mcpToolNames = model.tools.filter(isMCPServer).flatMap(s => s.tools);
    const mcpImport = mcpToolNames.length > 0
        ? `from tools.mcpClients import ${mcpToolNames.join(', ')}`
        : '';
    const pythonToolImports = model.tools
        .filter(isPythonTool)
        .map(pt => `from tools.${pt.modulePath} import ${pt.name}`)
        .join('\n');

    const profileNames = model.profiles.map(p => p.name.toUpperCase()).join(', ');

    const structuredOutputs = model.agents
        .map(generateStructuredOutput)
        .filter(s => s !== '')
        .join('\n\n');

    const models = model.agents
        .map(generateModel)
        .join('\n');

    const nodes = model.agents
        .map(generateNode)
        .join('\n\n');

    // Dict de despacho de tools para el while-loop en nodos async.
    const allToolNames = [
        ...mcpToolNames,
        ...model.tools.filter(isPythonTool).map(pt => pt.name),
    ];
    const toolsByName = isUsingTools(model)
        ? `_tools_by_name = {t.name: t for t in [${allToolNames.join(', ')}]}`
        : '';


    const fileNode = expandToNode`
# agents.py
${messageImports}
from prompt import ${profileNames}
from state import State
from langchain.chat_models import init_chat_model
${usesOllama ? 'from config import OLLAMA_BASE_URL' : ''}
${hasStructuredOutputs ? 'from pydantic import BaseModel, Field' : ''}
${mcpImport}
${pythonToolImports}

# Salidas de los nodos
${structuredOutputs}

# Modelos
${models}

${toolsByName}

# Nodos del grafo
${nodes}
`.appendNewLineIfNotEmpty();

    if (!fs.existsSync(data.destination)) {
        fs.mkdirSync(data.destination, { recursive: true });
    }
    fs.writeFileSync(generatedFilePath, toString(fileNode));
    return generatedFilePath;
}