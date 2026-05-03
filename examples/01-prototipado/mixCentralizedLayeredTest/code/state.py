# state.py
from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langgraph.graph.message import add_messages



class State(TypedDict):
    # Mensajes
    messages: Annotated[list, add_messages]

    # Atributos
    content: Optional[str]
    summary: Optional[str]
    score: Optional[int]
    approved: Optional[bool]
    report: Optional[str]


