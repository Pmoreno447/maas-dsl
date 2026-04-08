# state.py
from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]

    # Criterios para evaluar el CV
    candidateName: Optional[str]
    candidateEmail: Optional[str]
    yearsExperience: Optional[int]
    skills: Optional[str]
    educationLevel: Optional[str]
    language: Optional[str]

    # Datos de la evaluación
    score: Optional[int]
    meetRequirement: Optional[bool]
    strengths: Optional[str]
    weaknesses: Optional[str]

    # Datos del informe
    reportText: Optional[str]
    recommendation: Optional[str]