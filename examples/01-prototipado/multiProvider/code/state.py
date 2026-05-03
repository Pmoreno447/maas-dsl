# state.py
from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langgraph.graph.message import add_messages



class State(TypedDict):
    # Mensajes
    messages: Annotated[list, add_messages]

    # Atributos
    topic: Optional[str]
    research: Optional[str]
    draft: Optional[str]
    critique: Optional[str]
    finalText: Optional[str]


