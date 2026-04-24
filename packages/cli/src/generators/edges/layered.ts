import type { Layered, Layer } from 'multi-agent-dsl-language';
import { expandToNode, toString } from 'langium/generate';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { generateNodeName, subgraphDefinitionName } from '../../util.js'

function findStartLayer(layered: Layered): Layer {
    const referencedLayers = new Set(
        layered.layers
            .filter(l => l.next?.ref)
            .map(l => l.next!.ref!.name)
    );
    return layered.layers.find(l => !referencedLayers.has(l.name))!;
}

function getOrderedLayers(layered: Layered): Layer[] {
    const start = findStartLayer(layered);
    const ordered: Layer[] = [];
    let current: Layer | undefined = start;

    while (current) {
        ordered.push(current);
        current = current.next?.ref ?? undefined;
    }

    return ordered;
}

export function generateLayeredSubgraph(layered: Layered, destination: string): string {
    const layers = getOrderedLayers(layered);
    const subgraphDir = path.join(destination, 'subgraph');
    const filePath = path.join(subgraphDir, `${layered.name}.py`);

    const nodeImports = layers.map(l => generateNodeName(l.agent.ref!)).join(', ');

    const addNodes = layers
        .map(l => `builder.add_node("${l.agent.ref!.name.toLowerCase()}", ${generateNodeName(l.agent.ref!)})`)
        .join('\n    ');

    const edges: string[] = [];
    edges.push(`builder.add_edge(START, "${layers[0].agent.ref!.name.toLowerCase()}")`);
    for (let i = 0; i < layers.length - 1; i++) {
        const from = layers[i].agent.ref!.name.toLowerCase();
        const to = layers[i + 1].agent.ref!.name.toLowerCase();
        edges.push(`builder.add_edge("${from}", "${to}")`);
    }
    edges.push(`builder.add_edge("${layers[layers.length - 1].agent.ref!.name.toLowerCase()}", END)`);
    const addEdges = edges.join('\n    ');

    const definitionSubgraph = subgraphDefinitionName(layered) + '()';

    const fileNode = expandToNode`
from langgraph.graph import StateGraph, START, END
from state import State
from agents import ${nodeImports}

def ${definitionSubgraph}:
    builder = StateGraph(State)

    ${addNodes}

    ${addEdges}

    return builder.compile()
`.appendNewLineIfNotEmpty();

    if (!fs.existsSync(subgraphDir)) {
        fs.mkdirSync(subgraphDir, { recursive: true });
    }
    fs.writeFileSync(filePath, toString(fileNode));
    return filePath;
}
