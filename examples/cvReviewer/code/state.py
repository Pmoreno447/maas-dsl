# state.py
from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langgraph.graph.message import add_messages



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


