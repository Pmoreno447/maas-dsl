# agents.py
from langchain_core.messages import SystemMessage, HumanMessage
from prompt import COORDINATOR, ANALYZER, SUMMARIZER, FORMATTER, VALIDATOR, PUBLISHER
from state import State
from langchain.chat_models import init_chat_model

from pydantic import BaseModel, Field



# Salidas de los nodos
class FormatterOutput(BaseModel):
    report: str = Field(description="Informe final formateado listo para publicar")

class ValidatorOutput(BaseModel):
    approved: bool = Field(description="True si el contenido supera el umbral de calidad")

# Modelos
modelFormatter = init_chat_model(model="openai:gpt-4o-mini", temperature=0).with_structured_output(FormatterOutput)
modelValidator = init_chat_model(model="openai:gpt-4o-mini", temperature=0).with_structured_output(ValidatorOutput)
modelPublisher = init_chat_model(model="openai:gpt-4o-mini", temperature=0)



# Nodos del grafo
def nodeFormatter(state: State):
    """"""
    result = modelFormatter.invoke(
        [SystemMessage(content=FORMATTER)]
        + state["messages"]
        + [HumanMessage(content=f"""
            summary: {state["summary"]}
            score: {state["score"]}
        """)]
    )
    return {
        "report": result.report
    }

def nodeValidator(state: State):
    """"""
    result = modelValidator.invoke(
        [SystemMessage(content=VALIDATOR)]
        + state["messages"]
        + [HumanMessage(content=f"""
            report: {state["report"]}
            score: {state["score"]}
        """)]
    )
    return {
        "approved": result.approved
    }

def nodePublisher(state: State):
    """"""
    result = modelPublisher.invoke(
        [SystemMessage(content=PUBLISHER)]
        + state["messages"]
        + [HumanMessage(content=f"""
            report: {state["report"]}
            approved: {state["approved"]}
        """)]
    )
    return {"messages": [result]}
