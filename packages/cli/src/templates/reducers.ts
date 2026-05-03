import { isTrim, isMix, isSummarize, type Trim, type Mix, type None, type Summarize } from 'multi-agent-dsl-language';

// ─── Interfaz ────────────────────────────────────────────────────────────────

export interface MessageConfig {
    import: string;
    field: string;
    functionBefore: string;  // va antes de State (trim)
    functionAfter: string;   // va después de State (summarize)
}

// ─── Plantillas ───────────────────────────────────────────────────────────────

const TRIM: MessageConfig = {
    import: 'from config import MAX_MESSAGES',
    field: 'messages: Annotated[list, trim_messages_reducer(MAX_MESSAGES)]',
    functionBefore:
`def trim_messages_reducer(max_messages: int):
    """
    Devuelve un reducer que mantiene solo los últimos max_messages mensajes,
    conservando siempre el primero.
    """
    def reducer(current: list, new: list) -> list:
        updated = add_messages(current, new)
        if len(updated) > max_messages:
            return [updated[0]] + updated[-(max_messages - 1):]
        return updated
    return reducer`,
    functionAfter: '',
};

function buildSummarize(s: Summarize): MessageConfig {
    return {
        import:
`from langchain_core.messages import SystemMessage, RemoveMessage, BaseMessage
from langchain.chat_models import init_chat_model
from langgraph.graph import END
import tiktoken
from config import MAX_TOKENS`,
        field: 'messages: Annotated[list, add_messages]',
        functionBefore: '',
        functionAfter:
`llm = init_chat_model("${s.provider}:${s.model}")

def _count_tokens(messages: list[BaseMessage]) -> int:
    # tiktoken con encoding de OpenAI como aproximación universal (ver ADR 011).
    encoder = tiktoken.encoding_for_model("gpt-4o")
    return sum(
        len(encoder.encode(m.content))
        for m in messages
        if hasattr(m, "content") and isinstance(m.content, str)
    )

def should_summarize(state: State) -> str:
    return "summary_node" if _count_tokens(state["messages"]) > MAX_TOKENS else END

async def summary_node(state: State):
    messages = state["messages"]

    existing_summary = next(
        (m.content for m in messages if getattr(m, "name", None) == "__summary__"),
        None
    )

    if existing_summary:
        prompt = f"""
        Resumen previo: {existing_summary}
        Amplíalo con los nuevos mensajes manteniendo lo relevante:
        {messages}
        """
    else:
        prompt = f"Resume esta conversación de forma concisa: {messages}"

    new_summary = await llm.ainvoke(prompt)

    to_delete = [
        RemoveMessage(id=m.id)
        for m in messages[:-1]
        if getattr(m, "name", None) != "__summary__"
    ]

    return {
        "messages": [
            *to_delete,
            SystemMessage(content=new_summary.content, name="__summary__")
        ]
    }`,
    };
}

function buildMix(m: Mix): MessageConfig {
    return {
        import:
`from langchain_core.messages import SystemMessage, RemoveMessage, BaseMessage
from langchain.chat_models import init_chat_model
from langgraph.graph import END
import tiktoken
from config import MAX_MESSAGES, MAX_TOKENS`,
        field: 'messages: Annotated[list, trim_messages_reducer(MAX_MESSAGES)]',
        functionBefore:
`def trim_messages_reducer(max_messages: int):
    """
    Devuelve un reducer que mantiene solo los últimos max_messages mensajes,
    conservando siempre el primero.
    """
    def reducer(current: list, new: list) -> list:
        updated = add_messages(current, new)
        if len(updated) > max_messages:
            return [updated[0]] + updated[-(max_messages - 1):]
        return updated
    return reducer`,
        functionAfter:
`llm = init_chat_model("${m.provider}:${m.model}")

def _count_tokens(messages: list[BaseMessage]) -> int:
    # tiktoken con encoding de OpenAI como aproximación universal (ver ADR 011).
    encoder = tiktoken.encoding_for_model("gpt-4o")
    return sum(
        len(encoder.encode(m.content))
        for m in messages
        if hasattr(m, "content") and isinstance(m.content, str)
    )

def should_summarize(state: State) -> str:
    return "summary_node" if _count_tokens(state["messages"]) > MAX_TOKENS else END

async def summary_node(state: State):
    messages = state["messages"]

    existing_summary = next(
        (m.content for m in messages if getattr(m, "name", None) == "__summary__"),
        None
    )

    if existing_summary:
        prompt = f"""
        Resumen previo: {existing_summary}
        Amplíalo con los nuevos mensajes manteniendo lo relevante:
        {messages}
        """
    else:
        prompt = f"Resume esta conversación de forma concisa: {messages}"

    new_summary = await llm.ainvoke(prompt)

    to_delete = [
        RemoveMessage(id=m.id)
        for m in messages[:-1]
        if getattr(m, "name", None) != "__summary__"
    ]

    return {
        "messages": [
            *to_delete,
            SystemMessage(content=new_summary.content, name="__summary__")
        ]
    }`,
    };
}

const NONE: MessageConfig = {
    import: 'from langgraph.graph.message import add_messages',
    field: 'messages: Annotated[list, add_messages]',
    functionBefore: '',
    functionAfter: '',
};

// ─── Resolver ─────────────────────────────────────────────────────────────────

export function resolveMessageConfig(message: Trim | Mix | None | Summarize | undefined): MessageConfig {
    if (isTrim(message))      return TRIM;
    if (isSummarize(message)) return buildSummarize(message);
    if (isMix(message))       return buildMix(message);
    return NONE;
}

// ─── Inyección de nodo terminal en el grafo ───────────────────────────────────
// Estrategias que añaden un nodo al final del grafo (resumen, mix) exponen
// símbolos en state.py que el graphGenerator inserta sin saber qué estrategia es.
export interface TerminalNodeInjection {
    routerFn: string;        // función-router en state.py para conditional edge
    nodeName: string;        // nombre del nodo a añadir al builder
    stateImports: string[];  // símbolos a importar desde state
}

export function resolveTerminalNode(
    message: Trim | Mix | None | Summarize | undefined
): TerminalNodeInjection | null {
    if (isSummarize(message) || isMix(message)) {
        return {
            routerFn: 'should_summarize',
            nodeName: 'summary_node',
            stateImports: ['should_summarize', 'summary_node'],
        };
    }
    return null;
}