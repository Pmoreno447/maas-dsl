import type { LLMMultiAgentSystem, CommTransition, ConditionLiteral } from 'multi-agent-dsl-language';
import { isBoolLiteral, isIntLiteral, isStringLiteral } from 'multi-agent-dsl-language';
import { expandToNode, toString } from 'langium/generate';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { extractDestinationAndName, collectApiKeyEnvVars, subgraphDefinitionName } from '../util.js';
import { generateSubgraphs } from './edges/index.js';

// ─── Helpers ──────────────────────────────────────────────────────────────────
function generateConditionValue(literal: ConditionLiteral): string {
    if (isBoolLiteral(literal))   return literal.value ?? 'False';
    if (isIntLiteral(literal))    return String(literal.value);
    if (isStringLiteral(literal)) return `"${literal.value}"`;  // Langium ya stripea las comillas
    return '""';
}

function generateOperator(op: string): string {
    switch (op) {
        case 'equal':    return '==';
        case 'greather': return '>';
        case 'lower':    return '<';
        default:         return '==';
    }
}

function generateRouters(model: LLMMultiAgentSystem): { routers: string, edges: string } {
    const bySource = new Map<string, CommTransition[]>();
    for (const t of model.transitions) {
        const name = t.source.ref!.name;
        if (!bySource.has(name)) bySource.set(name, []);
        bySource.get(name)!.push(t);
    }

    const routerFns: string[] = [];
    const edgeCalls: string[] = [];

    for (const [sourceName, transitions] of bySource) {
        const srcNode = `"${sourceName.toLowerCase()}"`;
        const hasConditions = transitions.some(t => t.condition);

        if (!hasConditions) {
            const t = transitions[0];
            const target = t.isEnd ? 'END' : `"${t.target!.ref!.name.toLowerCase()}"`;
            edgeCalls.push(`builder.add_edge(${srcNode}, ${target})`);
            continue;
        }

        const fnName = `route_${sourceName.toLowerCase()}`;
        const lines: string[] = [`def ${fnName}(state: State) -> str:`];
        let defaultTarget = 'END';

        for (const t of transitions) {
            const target = t.isEnd ? 'END' : `"${t.target!.ref!.name.toLowerCase()}"`;
            if (t.condition) {
                const attr = t.condition.attribute.ref!.name;
                const op = generateOperator(t.condition.operator);
                const val = generateConditionValue(t.condition.value);
                lines.push(`    if state["${attr}"] ${op} ${val}:`);
                lines.push(`        return ${target}`);
            } else {
                defaultTarget = target;
            }
        }
        lines.push(`    return ${defaultTarget}`);
        routerFns.push(lines.join('\n'));

        const seen = new Set<string>();
        const mappingEntries = transitions
            .map(t => t.isEnd ? `        END: END` : `        "${t.target!.ref!.name.toLowerCase()}": "${t.target!.ref!.name.toLowerCase()}"`)
            .filter(v => !seen.has(v) && seen.add(v))
            .join(',\n');

        edgeCalls.push(`builder.add_conditional_edges(\n    ${srcNode},\n    ${fnName},\n    {\n${mappingEntries}\n    }\n)`);
    }

    return {
        routers: routerFns.join('\n\n'),
        edges:   edgeCalls.join('\n'),
    };
}

// ─── Generator ────────────────────────────────────────────────────────────────
export function generateGraph(model: LLMMultiAgentSystem, filePath: string, destination: string | undefined): string {
    const data = extractDestinationAndName(filePath, destination);
    const generatedFilePath = `${path.join(data.destination, 'graph')}.py`;

    generateSubgraphs(model, data.destination);

    const structures = model.communicationStructures;

    const subgraphImports = structures
        .map(s => `from subgraph.${s.name} import ${subgraphDefinitionName(s)}`)
        .join('\n');


    const initNodes = structures
        .map(s => `${s.name} = ${subgraphDefinitionName(s)}()`)
        .join('\n')

    const addNodes = structures
        .map(s => `builder.add_node("${s.name.toLowerCase()}", ${s.name})`)
        .join('\n');

    const startEdges = structures
        .filter(s => s.isStart)
        .map(s => `builder.add_edge(START, "${s.name.toLowerCase()}")`)
        .join('\n');

    const { routers, edges } = generateRouters(model);

    const apiKeys = collectApiKeyEnvVars(model.agents).filter(k => k !== 'OLLAMA_BASE_URL');
    const apiKeyImports = apiKeys.length > 0 ? `from config import ${apiKeys.join(', ')}` : '';
    const apiKeyEnvAssignments = apiKeys.map(k => `os.environ["${k}"] = ${k}`).join('\n');

    const fileNode = expandToNode`
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from state import State
import os
${subgraphImports}
${apiKeyImports}

${apiKeyEnvAssignments}


# Construcción del grafo
builder = StateGraph(State)

# Subgrafos como nodos
${initNodes}

${addNodes}

# Edges de inicio
${startEdges}

# Routers
${routers}

# Transiciones
${edges}

# Compilar
graph = builder.compile()

def print_state(result: dict):
    print("💬 MENSAJES:")
    for i, msg in enumerate(result.get("messages", [])):
        content = msg.content if hasattr(msg, "content") else str(msg)
        print(f"  [{i}] {type(msg).__name__}: {content}")

    print("📦 ESTADO:")
    for key, value in result.items():
        if key != "messages":
            print(f"  {key}: {value}")

# Ejecucion (Provisional)
import asyncio

async def main():
    entrada = """
    # Rellenar
"""
    result = await graph.ainvoke({
        "messages": [HumanMessage(content=entrada)]
    })
    print_state(result)

asyncio.run(main())`.appendNewLineIfNotEmpty();

    if (!fs.existsSync(data.destination)) {
        fs.mkdirSync(data.destination, { recursive: true });
    }
    fs.writeFileSync(generatedFilePath, toString(fileNode));
    return generatedFilePath;
}
