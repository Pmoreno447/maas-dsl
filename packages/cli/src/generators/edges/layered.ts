import type { Layered, Layer } from 'multi-agent-dsl-language';

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

export function generateLayeredEdges(layered: Layered): string {
    const layers = getOrderedLayers(layered);
    const edges: string[] = [];

    edges.push(`builder.add_edge(START, "${layers[0].agent.ref!.name.toLowerCase()}")`);

    for (let i = 0; i < layers.length - 1; i++) {
        const from = layers[i].agent.ref!.name.toLowerCase();
        const to = layers[i + 1].agent.ref!.name.toLowerCase();
        edges.push(`builder.add_edge("${from}", "${to}")`);
    }

    edges.push(`builder.add_edge("${layers[layers.length - 1].agent.ref!.name.toLowerCase()}", END)`);

    return edges.join('\n');
}