import type { LLMMultiAgentSystem } from 'multi-agent-dsl-language';
import { isLayered, isCentralized, isSharedMessagePool, isDecentralized } from 'multi-agent-dsl-language';
import { generateLayeredEdges } from './layered.js';
import { generateCentralizedEdges } from './centralized.js';

export function generateEdges(model: LLMMultiAgentSystem): string {
    return model.communicationStructures.map(structure => {
        if (isLayered(structure))           return generateLayeredEdges(structure);
        if (isCentralized(structure))       return generateCentralizedEdges();
        if (isSharedMessagePool(structure)) return '# SharedMessagePool: pendiente';
        if (isDecentralized(structure))     return '# Decentralized: pendiente';
        return '';
    }).join('\n');
}