import type { LLMMultiAgentSystem } from 'multi-agent-dsl-language';
import { isInMemorySaver, isPostgreSaver, isMongoDBSaver } from 'multi-agent-dsl-language';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { extractDestinationAndName } from '../util.js';
import { checkpointer } from '../templates/dbBlock.js'

// ─── Generator ────────────────────────────────────────────────────────────────

export function generateCheckpointer(model: LLMMultiAgentSystem, filePath: string, destination: string | undefined): void {
    const persistence = model.envirement.persistence;

    const data = extractDestinationAndName(filePath, destination);

    let content: string;
    if (isPostgreSaver(persistence)) {
        content = checkpointer.Postgre;
    } else if (isInMemorySaver(persistence)) {
        content = checkpointer.InMemorySaver;
    } else if (isMongoDBSaver(persistence)) {
        content = checkpointer.MongoDB;
    } else {
        return;
    }

    if (!fs.existsSync(data.destination)) {
        fs.mkdirSync(data.destination, { recursive: true });
    }

    fs.writeFileSync(path.join(data.destination, 'checkpointer.py'), content);
}
