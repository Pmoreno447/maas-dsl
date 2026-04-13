import type { LLMMultiAgentSystem } from 'multi-agent-dsl-language';
import { expandToNode, joinToNode, toString } from 'langium/generate';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { extractDestinationAndName } from '../util.js';

// ─── Generator ────────────────────────────────────────────────────────────────
export function generatePrompts(model: LLMMultiAgentSystem, filePath: string, destination: string | undefined): string {
    const data = extractDestinationAndName(filePath, destination);
    const generatedFilePath = `${path.join(data.destination, 'prompt')}.py`;

    const fileNode = expandToNode`
        ${joinToNode(model.profiles, profile => 
`${profile.name.toUpperCase()} = """ 
${profile.profileDescription.trim()}
"""
`, { appendNewLineIfNotEmpty: true })}
    `.appendNewLineIfNotEmpty();

    if (!fs.existsSync(data.destination)) {
        fs.mkdirSync(data.destination, { recursive: true });
    }
    fs.writeFileSync(generatedFilePath, toString(fileNode));
    return generatedFilePath;
}
