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

const SUMMARIZE: MessageConfig = {
    import:
`from langchain_core.messages import SystemMessage, RemoveMessage, BaseMessage
from langchain_openai import ChatOpenAI
import tiktoken
from config import MAX_TOKENS`,
    field: 'messages: Annotated[list, add_messages]',
    functionBefore: '',
    functionAfter:
`llm = ChatOpenAI(model="gpt-4o")

def count_tokens(messages: list[BaseMessage]) -> int:
    encoder = tiktoken.encoding_for_model("gpt-4o")
    return sum(
        len(encoder.encode(m.content))
        for m in messages
        if hasattr(m, "content") and isinstance(m.content, str)
    )

async def summary_node(state: State):
    messages = state["messages"]

    if count_tokens(messages) <= MAX_TOKENS:
        return {}

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

const MIX: MessageConfig = {
    import: '# Falta por desarrollar: mix',
    field: '# Falta por desarrollar: campo messages para mix',
    functionBefore: '# Falta por desarrollar: reducer para mix',
    functionAfter: '',
};

const NONE: MessageConfig = {
    import: 'from langgraph.graph.message import add_messages',
    field: 'messages: Annotated[list, add_messages]',
    functionBefore: '',
    functionAfter: '',
};

// ─── Resolver ─────────────────────────────────────────────────────────────────

export function resolveMessageConfig(message: Trim | Mix | None | Summarize | undefined): MessageConfig {
    if (isTrim(message))      return TRIM;
    if (isSummarize(message)) return SUMMARIZE;
    if (isMix(message))       return MIX;
    return NONE;
}