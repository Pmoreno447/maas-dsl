import type { LLMMultiAgentSystem, CommTransition, ConditionLiteral } from 'multi-agent-dsl-language';
import { isBoolLiteral, isIntLiteral, isStringLiteral } from 'multi-agent-dsl-language';
import { expandToNode, toString } from 'langium/generate';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { extractDestinationAndName, collectApiKeyEnvVars, subgraphDefinitionName} from '../util.js';
import { generateSubgraphs } from './edges/index.js';
import { resolveTerminalNode, type TerminalNodeInjection } from '../templates/reducers.js';


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

function generateRouters(model: LLMMultiAgentSystem, terminal: TerminalNodeInjection | null): { routers: string, edges: string } {
    const bySource = new Map<string, CommTransition[]>();
    for (const t of model.transitions) {
        if (t.isStart) continue;
        const name = t.source!.ref!.name;
        if (!bySource.has(name)) bySource.set(name, []);
        bySource.get(name)!.push(t);
    }

    const routerFns: string[] = [];
    const edgeCalls: string[] = [];

    const endReturn = terminal ? `${terminal.routerFn}(state)` : 'END';

    for (const [sourceName, transitions] of bySource) {
        const srcNode = `"${sourceName.toLowerCase()}"`;
        const hasConditions = transitions.some(t => t.condition);

        if (!hasConditions) {
            const t = transitions[0];
            if (t.isEnd && terminal) {
                edgeCalls.push(`builder.add_conditional_edges(\n    ${srcNode},\n    ${terminal.routerFn},\n    {\n        "${terminal.nodeName}": "${terminal.nodeName}",\n        END: END\n    }\n)`);
            } else {
                const target = t.isEnd ? 'END' : `"${t.target!.ref!.name.toLowerCase()}"`;
                edgeCalls.push(`builder.add_edge(${srcNode}, ${target})`);
            }
            continue;
        }

        const fnName = `route_${sourceName.toLowerCase()}`;
        const lines: string[] = [`def ${fnName}(state: State) -> str:`];
        const defaultsToEnd = !transitions.some(t => !t.condition);
        let defaultTarget = endReturn;
        let usesEnd = defaultsToEnd;

        for (const t of transitions) {
            const target = t.isEnd ? endReturn : `"${t.target!.ref!.name.toLowerCase()}"`;
            if (t.isEnd) usesEnd = true;
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
        const mappingEntries: string[] = [];
        for (const t of transitions) {
            const entry = t.isEnd ? `        END: END` : `        "${t.target!.ref!.name.toLowerCase()}": "${t.target!.ref!.name.toLowerCase()}"`;
            if (!seen.has(entry)) { seen.add(entry); mappingEntries.push(entry); }
        }
        if (defaultsToEnd) {
            const endEntry = `        END: END`;
            if (!seen.has(endEntry)) { seen.add(endEntry); mappingEntries.push(endEntry); }
        }
        if (terminal && usesEnd) {
            mappingEntries.push(`        "${terminal.nodeName}": "${terminal.nodeName}"`);
        }

        edgeCalls.push(`builder.add_conditional_edges(\n    ${srcNode},\n    ${fnName},\n    {\n${mappingEntries.join(',\n')}\n    }\n)`);
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

    const startEdges = model.transitions
        .filter(t => t.isStart && t.target?.ref)
        .map(t => `builder.add_edge(START, "${t.target!.ref!.name.toLowerCase()}")`)
        .join('\n');

    const terminal = resolveTerminalNode(model.envirement.messages);
    const { routers, edges } = generateRouters(model, terminal);

    const apiKeys = collectApiKeyEnvVars(model.agents).filter(k => k !== 'OLLAMA_BASE_URL');
    const apiKeyImports = apiKeys.length > 0 ? `from config import ${apiKeys.join(', ')}` : '';
    const apiKeyEnvAssignments = apiKeys.map(k => `os.environ["${k}"] = ${k}`).join('\n');

    const stateImport = terminal
        ? `from state import State, ${terminal.stateImports.join(', ')}`
        : 'from state import State';

    const terminalNodeRegistration = terminal
        ? `builder.add_node("${terminal.nodeName}", ${terminal.nodeName})\nbuilder.add_edge("${terminal.nodeName}", END)`
        : '';

    const fileNode = expandToNode`
import os
${apiKeyImports}
${apiKeyEnvAssignments}
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
${stateImport}
${subgraphImports}



# Construcción del grafo
builder = StateGraph(State)

# Subgrafos como nodos
${initNodes}

${addNodes}

${terminalNodeRegistration}

# Edges de inicio
${startEdges}

# Routers
${routers}

# Transiciones
${edges}

# Compilar
graph = builder.compile()`.appendNewLineIfNotEmpty();

    if (!fs.existsSync(data.destination)) {
        fs.mkdirSync(data.destination, { recursive: true });
    }
    fs.writeFileSync(generatedFilePath, toString(fileNode));
    return generatedFilePath;
}
