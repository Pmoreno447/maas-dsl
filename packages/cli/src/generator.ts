import { generatePrompts } from './generators/promptGenerator.js';
import { stateGenerator } from './generators/stateGenerator.js'
import { generateEnvFiles } from './generators/configGenerator.js'
import { agentsGenerator } from './generators/agentsGenerator.js'
import { generateGraph } from './generators/graphGenerator.js'
import { mcpClientGenerator } from './generators/mcpClientGenerator.js'
import { generateLangGraphJson } from './generators/jsonGenerator.js'
import { generateCheckpointer } from './generators/checkpointerGenerator.js'
import type { LLMMultiAgentSystem } from 'multi-agent-dsl-language';

export function generate(model: LLMMultiAgentSystem, filePath: string, destination: string | undefined): void {
    generatePrompts(model, filePath, destination);
    stateGenerator(model, filePath, destination);
    generateEnvFiles(model, filePath, destination);
    mcpClientGenerator(model, filePath, destination);
    agentsGenerator(model, filePath, destination);
    generateGraph(model, filePath, destination);
    generateLangGraphJson(model, filePath, destination);
    generateCheckpointer(model, filePath, destination);
}