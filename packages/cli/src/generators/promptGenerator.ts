import type { LLMMultiAgentSystem, Profile } from 'multi-agent-dsl-language';
import { isCentralized } from 'multi-agent-dsl-language';
import { expandToNode, joinToNode, toString } from 'langium/generate';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { extractDestinationAndName } from '../util.js';

function collectAllProfiles(model: LLMMultiAgentSystem): Profile[] {
    const seen = new Set<string>();
    const profiles: Profile[] = [];

    for (const p of model.profiles) {
        if (!seen.has(p.name)) { seen.add(p.name); profiles.push(p); }
    }

    for (const s of model.communicationStructures) {
        if (!isCentralized(s)) continue;
        const p = s.coordinator.profile.ref;
        if (p && !seen.has(p.name)) { seen.add(p.name); profiles.push(p); }
    }

    return profiles;
}

// ─── Generator ────────────────────────────────────────────────────────────────
export function generatePrompts(model: LLMMultiAgentSystem, filePath: string, destination: string | undefined): string {
    const data = extractDestinationAndName(filePath, destination);
    const generatedFilePath = `${path.join(data.destination, 'prompt')}.py`;

    const allProfiles = collectAllProfiles(model);

    const fileNode = expandToNode`
        ${joinToNode(allProfiles, profile =>
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
