import type { LLMMultiAgentSystem } from 'multi-agent-dsl-language';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { extractDestinationAndName, isDb } from '../util.js';
import { type InMemorySaver, type PostgreSaver, type MongoDBSaver } from 'multi-agent-dsl-language';

function buildCheckpointerField(persistenceType: InMemorySaver | PostgreSaver | MongoDBSaver) {
    if (isDb(persistenceType)) {
        return { path: './checkpointer.py:generate_checkpointer' };
    }
    return undefined;
}

// ─── Generator ────────────────────────────────────────────────────────────────
export function generateLangGraphJson(model: LLMMultiAgentSystem, filePath: string, destination: string | undefined): void {
    const data = extractDestinationAndName(filePath, destination);
    const generatedFilePath = path.join(data.destination, 'langgraph.json');

    const checkpointer = buildCheckpointerField(model.envirement.persistence);

    const config: Record<string, unknown> = {
        dependencies: ['.'],
        graphs: {
            agent: './graph.py:graph',
        },
        ...(checkpointer ? { checkpointer } : {}),
        env: '.env',
    };

    if (!fs.existsSync(data.destination)) {
        fs.mkdirSync(data.destination, { recursive: true });
    }

    fs.writeFileSync(generatedFilePath, JSON.stringify(config, null, 2) + '\n');
}
