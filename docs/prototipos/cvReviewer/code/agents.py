from pydantic import BaseModel, Field # Structured outputs

from langchain_core.messages import SystemMessage, HumanMessage # SOLO SI HAY HERRAMIENTAS, ToolMessage
from prompt import EXTRACTOR, EVALUATOR, REPORT_GENERATOR, NOTIFIER
from state import State
from langchain.chat_models import init_chat_model

from tools.notifyByEmail import notifyByEmail
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
      
# Salidas de los nodos 
# Structured output del Extractor
class ExtractorOutput(BaseModel):
    candidateName: str = Field(description="Nombre completo del candidato")
    candidateEmail: str = Field(description="Correo electrónico del candidato")
    yearsExperience: int = Field(description="Años totales de experiencia profesional")
    skills: str = Field(description="Lista de habilidades técnicas del candidato")
    educationLevel: str = Field(description="Nivel de estudios más alto (grado, máster, doctorado)")
    language: str = Field(description="Idiomas y nivel de competencia del candidato")

class EvaluatorOutput(BaseModel):
    score: int = Field(description="Puntuación del candidato del 0 al 10")
    meetRequirement: bool = Field(description="Indica si el candidato cumple los requisitos mínimos del puesto")
    strengths: str = Field(description="Puntos fuertes del candidato relevantes para el puesto")
    weaknesses: str = Field(description="Puntos débiles o requisitos que no cumple el candidato")

class ReportGeneratorOutput(BaseModel):
    reportText: str = Field(description="Informe profesional y conciso para el equipo de RRHH")
    recommendation: str = Field(description="Recomendación final: 'contratar', 'descartar' o 'considerar'")


# Modelos
modeloExtractor = init_chat_model(model="openai:gpt-5-nano", temperature=0).with_structured_output(ExtractorOutput)
modeloEvaluator = init_chat_model(model="openai:gpt-5-nano", temperature=0).with_structured_output(EvaluatorOutput)
modeloReportGenerator = init_chat_model(model="openai:gpt-5-nano", temperature=0).with_structured_output(ReportGeneratorOutput)
modeloNotifier = init_chat_model(model="openai:gpt-5-nano", temperature=0).bind_tools([notifyByEmail])

# Nodos del grafo
def nodoExtractor(state):
    """Extrae la información relevante del CV"""
    result = modeloExtractor.invoke(
        [SystemMessage(content=EXTRACTOR)]
        + state["messages"]
    )
    return {
        "candidateName": result.candidateName,
        "candidateEmail": result.candidateEmail,
        "yearsExperience": result.yearsExperience,
        "skills": result.skills,
        "educationLevel": result.educationLevel,
        "language": result.language
    }


def nodoEvaluator(state):
    """Evalúa al candidato según los requisitos del puesto"""
    result = modeloEvaluator.invoke(
        [SystemMessage(content=EVALUATOR)]
        + state["messages"]
        + [HumanMessage(content=f"""
            candidateName: {state["candidateName"]}
            candidateEmail: {state["candidateEmail"]}
            yearsExperience: {state["yearsExperience"]}
            skills: {state["skills"]}
            educationLevel: {state["educationLevel"]}
            language: {state["language"]}
        """)]
    )
    return {
        "score": result.score,
        "meetRequirement": result.meetRequirement,
        "strengths": result.strengths,
        "weaknesses": result.weaknesses
    }


def nodoReportGenerator(state):
    """Genera el informe final para el equipo de RRHH"""
    result = modeloReportGenerator.invoke(
        [SystemMessage(content=REPORT_GENERATOR)]
        + state["messages"]
        + [HumanMessage(content=f"""
            candidateName: {state["candidateName"]}
            yearsExperience: {state["yearsExperience"]}
            skills: {state["skills"]}
            educationLevel: {state["educationLevel"]}
            language: {state["language"]}
            score: {state["score"]}
            meetRequirement: {state["meetRequirement"]}
            strengths: {state["strengths"]}
            weaknesses: {state["weaknesses"]}
        """)]
    )
    return {
        "reportText": result.reportText,
        "recommendation": result.recommendation
    }

async def nodoNotifier(state):
    """Notifica al candidato si su puntuación supera el umbral"""
    messages = (
        [SystemMessage(content=NOTIFIER)]
        + state["messages"]
        + [HumanMessage(content=f"""
            Nombre: {state["candidateName"]}
            Email: {state["candidateEmail"]}
            Puntuación: {state["score"]}
            Informe: {state["reportText"]}
            Recomendación: {state["recommendation"]}
        """)]
    )

    while True:
        response = await modeloNotifier.ainvoke(messages)
        messages.append(response)

        if not response.tool_calls:
            break

        for tc in response.tool_calls:
            result = await notifyByEmail.ainvoke(tc["args"])
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    return {"messages": [response]}