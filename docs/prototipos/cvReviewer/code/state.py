# state.py
from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

def trim_messages_reducer(max_messages: int):
    """
    Devuelve un reducer que mantiene solo los últimos max_messages mensajes,
    conservando siempre el primero.
    """
    def reducer(current: list, new: list) -> list:
        # Primero aplica add_messages para gestionar correctamente los IDs
        updated = add_messages(current, new)
        
        # Conserva el primer mensaje (CV) + los últimos (max_messages - 1)
        if len(updated) > max_messages:
            return [updated[0]] + updated[-(max_messages - 1):]
        return updated
    
    return reducer

class State(TypedDict):
    # messages: Annotated[list, add_messages]
    messages: Annotated[list, trim_messages_reducer(max_messages=2)]

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