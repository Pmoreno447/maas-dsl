# state.py
from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langgraph.graph.message import add_messages



class State(TypedDict):
    # Mensajes
    messages: Annotated[list, add_messages]

    # Atributos
    isValid: Optional[bool]
    orderId: Optional[str]
    issueDescription: Optional[str]
    preferredSolution: Optional[str]
    orderStatus: Optional[str]
    productID: Optional[str]
    productBatch: Optional[str]
    trackingNumber: Optional[str]
    paymentAmount: Optional[int]
    paymentStatus: Optional[str]
    decision: Optional[str]


