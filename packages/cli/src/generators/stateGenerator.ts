import type { LLMMultiAgentSystem } from 'multi-agent-dsl-language';
import { expandToNode, joinToNode, toString } from 'langium/generate';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { extractDestinationAndName } from '../util.js';
import { isTrim, isMix, isNone, isSummarize, type Trim, type Mix, type None, type Summarize } from 'multi-agent-dsl-language';
import { resolveMessageConfig } from '../templates/reducers.js'
import { toPythonType } from '../util.js';

export function stateGenerator(model: LLMMultiAgentSystem, filePath: string, destination: string | undefined): string {
    const data = extractDestinationAndName(filePath, destination);
    const generatedFilePath = `${path.join(data.destination, 'state')}.py`;

    // Lógica FUERA del template
    const message = resolveMessageConfig(model.envirement.messages)

    // Template SOLO con strings y ${variables}
    const fileNode = expandToNode
`
# state.py
from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
${message.import}

${message.function}

class State(TypedDict):
    # Mensajes
    ${message.field}

    # Atributos
${joinToNode(model.envirement.attributes, attribute =>
`    ${attribute.name}: Optional[${toPythonType(attribute.type)}]`
, { appendNewLineIfNotEmpty: true })}
`.appendNewLineIfNotEmpty();

    if (!fs.existsSync(data.destination)) {
        fs.mkdirSync(data.destination, { recursive: true });
    }
    fs.writeFileSync(generatedFilePath, toString(fileNode));
    return generatedFilePath;
}