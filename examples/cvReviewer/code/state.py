# state.py
from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage, RemoveMessage, BaseMessage
from langchain_openai import ChatOpenAI
import tiktoken
from config import MAX_TOKENS

llm = ChatOpenAI(model="gpt-4o")

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
    }

class State(TypedDict):
    # Mensajes
    messages: Annotated[list, add_messages]

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
