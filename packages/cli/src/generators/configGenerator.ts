import type { LLMMultiAgentSystem } from 'multi-agent-dsl-language';
import { expandToNode, toString } from 'langium/generate';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { extractDestinationAndName, collectApiKeyEnvVars, collectMcpApiKeyEnvVars } from '../util.js';
import { isTrim, isMix, isSummarize, type Trim, type Mix, type None, type Summarize } from 'multi-agent-dsl-language';

// Defaults razonables para variables de entorno que no son secretos sino
// endpoints (ej. Ollama corre en localhost por defecto).
const ENV_DEFAULTS: Record<string, string> = {
    OLLAMA_BASE_URL: 'http://localhost:11434'
};

// ─── Helpers ──────────────────────────────────────────────────────────────────
function resolveMessageEnvVars(message: Trim | Mix | None | Summarize | undefined): string {
    if (isTrim(message)) {
        return `MAX_MESSAGES=${message.maxMessages}`;
    } else if (isSummarize(message)) {
        return `MAX_TOKENS=${message.maxToken}`;
    } else if (isMix(message)) {
        return `MAX_MESSAGES=${message.maxMessages}
MAX_TOKENS=${message.maxToken}`;
    }
    return '';
}

function resolveMessageConfigVars(message: Trim | Mix | None | Summarize | undefined): string {
    if (isTrim(message)) {
        return `MAX_MESSAGES = int(os.getenv("MAX_MESSAGES", 10))`;
    } else if (isSummarize(message)) {
        return `MAX_TOKENS = int(os.getenv("MAX_TOKENS", 1000))`;
    } else if (isMix(message)) {
        return `MAX_MESSAGES = int(os.getenv("MAX_MESSAGES", 10))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 1000))`;
    }
    return '';
}

// ─── Generator ────────────────────────────────────────────────────────────────
export function generateEnvFiles(model: LLMMultiAgentSystem, filePath: string, destination: string | undefined): void {
    const data = extractDestinationAndName(filePath, destination);

    const messageEnvVars = resolveMessageEnvVars(model.envirement.messages);
    const messageConfigVars = resolveMessageConfigVars(model.envirement.messages);

    const apiKeys = [
        ...collectApiKeyEnvVars(model.agents),
        ...collectMcpApiKeyEnvVars(model.tools)
    ];
    const envApiKeys = apiKeys.map(k => `${k}=`).join('\n');
    const configApiKeys = apiKeys.map(k => {
        const fallback = ENV_DEFAULTS[k];
        return fallback
            ? `${k} = os.getenv("${k}", "${fallback}")`
            : `${k} = os.getenv("${k}")`;
    }).join('\n');

    // Genera .env.template
    const envNode = expandToNode`
# API Keys
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=
${envApiKeys}

# Configuración de mensajes
${messageEnvVars}
`.appendNewLineIfNotEmpty();

    // Genera config.py
    const configNode = expandToNode`
# config.py — ARCHIVO GENERADO AUTOMÁTICAMENTE — NO EDITAR A MANO
from dotenv import load_dotenv
import os

load_dotenv()

LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT")
${configApiKeys}

# Configuración de mensajes
${messageConfigVars}
`.appendNewLineIfNotEmpty();

    if (!fs.existsSync(data.destination)) {
        fs.mkdirSync(data.destination, { recursive: true });
    }

    fs.writeFileSync(path.join(data.destination, '.env.template'), toString(envNode));
    fs.writeFileSync(path.join(data.destination, 'config.py'), toString(configNode));
}
