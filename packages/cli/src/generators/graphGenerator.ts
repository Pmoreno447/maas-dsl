import type { Agent, LLMMultiAgentSystem } from 'multi-agent-dsl-language';
import { expandToNode, toString } from 'langium/generate';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { extractDestinationAndName } from '../util.js';
import { generateNodeName } from '../util.js'
import { generateEdges } from './edges/index.js'

// ─── Helpers ──────────────────────────────────────────────────────────────────
function generateRegisterNode(agent: Agent): string {
    const registerNode = 'builder.add_node("' + agent.name.toLowerCase() + '", ' + generateNodeName(agent) + ')'
    return registerNode;
}

// ─── Generator ────────────────────────────────────────────────────────────────
export function generateGraph(model: LLMMultiAgentSystem, filePath: string, destination: string | undefined): string {
    const data = extractDestinationAndName(filePath, destination);
    const generatedFilePath = `${path.join(data.destination, 'graph')}.py`;

    const nodeNames = model.agents.map(a => generateNodeName(a)).join(', ');
    const addNodes = model.agents.map(a => generateRegisterNode(a)).join('\n'); 

    const edges = generateEdges(model);

    const fileNode = expandToNode
`from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from state import State
import os
from config import OPENAI_API_KEY

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY # HARDCODEADO EN EL GENERADOR, PROVISIONAL

from agents import ${nodeNames}

# Construcción del grafo
builder = StateGraph(State)

# Nodos
${addNodes}

# Edges
${edges}

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

print_state(result)`.appendNewLineIfNotEmpty();

    if (!fs.existsSync(data.destination)) {
        fs.mkdirSync(data.destination, { recursive: true });
    }
    fs.writeFileSync(generatedFilePath, toString(fileNode));
    return generatedFilePath;
}
