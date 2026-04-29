import type { LLMMultiAgentSystem, Agent } from 'multi-agent-dsl-language';
import { isMCPServer, isCentralized, isPostgreSaver, isMongoDBSaver, isSummarize } from 'multi-agent-dsl-language';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { extractDestinationAndName } from '../util.js';

// ─── Helpers ──────────────────────────────────────────────────────────────────

const BASE_REQUIREMENTS = [
    'langgraph',
    'langchain',
    'langchain-core',
    'python-dotenv',
    'pydantic',
    'typing-extensions',
    'langsmith',
];

function providerRequirement(provider: string): string | null {
    switch (provider) {
        case 'openai':    return 'langchain-openai';
        case 'anthropic': return 'langchain-anthropic';
        case 'google':    return 'langchain-google-genai';
        case 'ollama':    return 'langchain-ollama';
        default:          return null;
    }
}

function collectProviderRequirements(model: LLMMultiAgentSystem): string[] {
    const providers = new Set<string>();
    for (const agent of model.agents as Agent[]) {
        providers.add(agent.provider);
    }
    for (const comm of model.communicationStructures) {
        if (isCentralized(comm)) providers.add(comm.coordinator.provider);
    }
    return [...providers]
        .map(providerRequirement)
        .filter((r): r is string => r !== null);
}

function hasMcpTools(model: LLMMultiAgentSystem): boolean {
    return model.tools.some(isMCPServer);
}

function persistenceRequirements(model: LLMMultiAgentSystem): string[] {
    const persistence = model.envirement.persistence;
    if (isPostgreSaver(persistence)) {
        return ['langgraph-checkpoint-postgres', 'psycopg[binary]'];
    }
    if (isMongoDBSaver(persistence)) {
        return ['langgraph-checkpoint-mongodb', 'pymongo'];
    }
    return [];
}

// ─── Generator ────────────────────────────────────────────────────────────────

export function generateRequirements(model: LLMMultiAgentSystem, filePath: string, destination: string | undefined): void {
    const data = extractDestinationAndName(filePath, destination);

    const requirements = new Set<string>(BASE_REQUIREMENTS);

    for (const r of collectProviderRequirements(model)) requirements.add(r);
    if (hasMcpTools(model)) requirements.add('langchain-mcp-adapters');
    for (const r of persistenceRequirements(model)) requirements.add(r);
    if (isSummarize(model.envirement.messages)) {
        // El reducer de summarize usa ChatOpenAI + tiktoken (ver templates/reducers.ts).
        requirements.add('langchain-openai');
        requirements.add('tiktoken');
    }

    const content = [...requirements].sort().join('\n') + '\n';

    if (!fs.existsSync(data.destination)) {
        fs.mkdirSync(data.destination, { recursive: true });
    }
    fs.writeFileSync(path.join(data.destination, 'requirements.txt'), content);
}
