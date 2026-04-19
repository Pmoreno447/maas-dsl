import type { LLMMultiAgentSystem, Agent } from 'multi-agent-dsl-language';
import { expandToNode, toString } from 'langium/generate';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { extractDestinationAndName, toPythonType, toModel, generateNodeName } from '../util.js';

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

    return `class ${className}(BaseModel):\n${fields}`;
}

function generateModel(agent: Agent): string {
    const variableName = 'model' + agent.name.charAt(0).toUpperCase() + agent.name.slice(1);
    const className = agent.name.charAt(0).toUpperCase() + agent.name.slice(1) + 'Output';

    const params: string[] = [
        `model="${toModel(agent)}"`,
        `temperature=${agent.temperature ?? 0}`,
    ];
    if (agent.maxToken)   params.push(`max_tokens=${agent.maxToken}`);
    if (agent.timeOut)    params.push(`timeout=${agent.timeOut}`);
    if (agent.maxRetries) params.push(`max_retries=${agent.maxRetries}`);

    let line = `${variableName} = init_chat_model(${params.join(', ')})`;

    if (agent.stateUpdate && agent.stateUpdate.length > 0) {
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

    const contextFields = agent.stateContext && agent.stateContext.length > 0
        ? `+ [HumanMessage(content=f"""
${agent.stateContext.map(ref => `            ${ref.ref!.name}: {state["${ref.ref!.name}"]}`).join('\n')}
        """)]`
        : '';

    const returnBlock = agent.stateUpdate && agent.stateUpdate.length > 0
        ? `return {\n${agent.stateUpdate.map(ref =>
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


    const fileNode = expandToNode`
# agents.py
${messageImports}
from prompt import ${profileNames}
from state import State
from langchain.chat_models import init_chat_model
${hasStructuredOutputs ? 'from pydantic import BaseModel, Field' : ''}
# Importar herramientas (pendiente siguiente iteración)

# Salidas de los nodos 
${structuredOutputs}

# Modelos
${models}

# Nodos del grafo
${nodes}
`.appendNewLineIfNotEmpty();

    if (!fs.existsSync(data.destination)) {
        fs.mkdirSync(data.destination, { recursive: true });
    }
    fs.writeFileSync(generatedFilePath, toString(fileNode));
    return generatedFilePath;
}