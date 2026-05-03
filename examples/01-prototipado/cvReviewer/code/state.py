# state.py
from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage, RemoveMessage, BaseMessage
from langchain.chat_models import init_chat_model
from langgraph.graph import END
import tiktoken
from config import MAX_MESSAGES, MAX_TOKENS

def trim_messages_reducer(max_messages: int):
    """
    Devuelve un reducer que mantiene solo los últimos max_messages mensajes,
    conservando siempre el primero.
    """
    def reducer(current: list, new: list) -> list:
        updated = add_messages(current, new)
        if len(updated) > max_messages:
            return [updated[0]] + updated[-(max_messages - 1):]
        return updated
    return reducer

class State(TypedDict):
    # Mensajes
    messages: Annotated[list, trim_messages_reducer(MAX_MESSAGES)]

    # Atributos
    candidateName: Optional[str]
    candidateEmail: Optional[str]
    yearsExperience: Optional[int]
    skills: Optional[str]
    educationLevel: Optional[str]
    language: Optional[str]
    score: Optional[int]
    meetRequirement: Optional[bool]
    strengths: Optional[str]
    weaknesses: Optional[str]
    reportText: Optional[str]
    recommendation: Optional[str]

llm = init_chat_model("openai:gpt-5-nano")

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
    }
