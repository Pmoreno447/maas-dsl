import type { LLMMultiAgentSystem } from 'multi-agent-dsl-language';
import { isLayered, isCentralized, isSharedMessagePool, isDecentralized } from 'multi-agent-dsl-language';
import { generateLayeredSubgraph } from './layered.js';
import { generateCentralizedEdges } from './centralized.js';

export function generateSubgraphs(model: LLMMultiAgentSystem, destination: string): void {
    for (const structure of model.communicationStructures) {
        if (isLayered(structure))           { generateLayeredSubgraph(structure, destination); continue; }
        if (isCentralized(structure))       { generateCentralizedEdges(); continue; }
        if (isSharedMessagePool(structure)) { continue; }
        if (isDecentralized(structure))     { continue; }
    }
}
