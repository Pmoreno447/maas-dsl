import type { AstNode, LangiumCoreServices, LangiumDocument } from 'langium';
import chalk from 'chalk';
import * as path from 'node:path';
import * as fs from 'node:fs';
import { URI } from 'langium';
import type { Agent } from 'multi-agent-dsl-language';
import { isKnownProvider } from 'multi-agent-dsl-language';


export async function extractDocument(fileName: string, services: LangiumCoreServices): Promise<LangiumDocument> {
    const extensions = services.LanguageMetaData.fileExtensions;
    if (!extensions.includes(path.extname(fileName))) {
        console.error(chalk.yellow(`Please choose a file with one of these extensions: ${extensions}.`));
        process.exit(1);
    }

    if (!fs.existsSync(fileName)) {
        console.error(chalk.red(`File ${fileName} does not exist.`));
        process.exit(1);
    }

    const document = await services.shared.workspace.LangiumDocuments.getOrCreateDocument(URI.file(path.resolve(fileName)));
    await services.shared.workspace.DocumentBuilder.build([document], { validation: true });

    const validationErrors = (document.diagnostics ?? []).filter(e => e.severity === 1);
    if (validationErrors.length > 0) {
        console.error(chalk.red('There are validation errors:'));
        for (const validationError of validationErrors) {
            console.error(chalk.red(
                `line ${validationError.range.start.line + 1}: ${validationError.message} [${document.textDocument.getText(validationError.range)}]`
            ));
        }
        process.exit(1);
    }

    return document;
}

export async function extractAstNode<T extends AstNode>(fileName: string, services: LangiumCoreServices): Promise<T> {
    return (await extractDocument(fileName, services)).parseResult?.value as T;
}

interface FilePathData {
    destination: string,
    name: string
}

export function extractDestinationAndName(filePath: string, destination: string | undefined): FilePathData {
    filePath = path.basename(filePath, path.extname(filePath)).replace(/[.-]/g, '');
    return {
        destination: destination ?? path.join(path.dirname(filePath), 'generated'),
        name: path.basename(filePath)
    };
}

export function toPythonType(type: string): string {
    switch (type) {
        case 'int':     return 'int';
        case 'float':   return 'float';
        case 'string':  return 'str';
        case 'boolean': return 'bool';
        default:        return 'str';
    }
}

export function toModel(agent: Agent): string {
    return `${agent.provider}:${agent.model}`;
}

export function generateNodeName(agent: Agent): string {
    const agentPascal = agent.name.charAt(0).toUpperCase() + agent.name.slice(1);
    return `node${agentPascal}`;
}

export function resolveApiKeyEnvVar(agent: Agent): string | null {
    if (!isKnownProvider(agent.provider)) return null;
    switch (agent.provider) {
        case 'openai':    return 'OPENAI_API_KEY';
        case 'anthropic': return 'ANTHROPIC_API_KEY';
        case 'google':    return 'GOOGLE_API_KEY';
        case 'ollama':    return 'OLLAMA_BASE_URL';
    }
}

export function collectApiKeyEnvVars(agents: Agent[]): string[] {
    const keys = new Set<string>();
    for (const agent of agents) {
        const key = resolveApiKeyEnvVar(agent);
        if (key) keys.add(key);
    }
    return [...keys];
}
