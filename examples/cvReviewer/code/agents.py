# agents.py
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from prompt import EXTRACTOR, EVALUATOR, REPORTGENERATOR, NOTIFIER
from state import State
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
# Importar herramientas (pendiente siguiente iteración)

# Salidas de los nodos 
class ExtractorOutput(BaseModel):
    candidateName: str = Field(description="Nombre del candidato")
    candidateEmail: str = Field(description="Email del candidato")
    yearsExperience: int = Field(description="Años de experiencia del candidato")
    skills: str = Field(description="Habilidades concretas del candidato")
    educationLevel: str = Field(description="Estudios superiores del candidato")
    language: str = Field(description="Idiomas que habla el candidato")

class EvaluatorOutput(BaseModel):
    score: int = Field(description="Puntuación otorgada del 1 al 10")
    meetRequirement: bool = Field(description="True si cumple los requisitos de puntuación, false si no lo hace")
    strengths: str = Field(description="Puntos fuertes del candidato")
    weaknesses: str = Field(description="Puntos débiles del candidato")

class ReportGeneratorOutput(BaseModel):
    reportText: str = Field(description="Texto resumen del candidato")
    recommendation: str = Field(description="Solo puede ser uno de los siguientes valores: Contratar, Descartar, Considerar")

# Modelos
modelExtractor = init_chat_model(model="openai:gpt-5-nano", temperature=0).with_structured_output(ExtractorOutput)
modelEvaluator = init_chat_model(model="openai:gpt-5-nano", temperature=0).with_structured_output(EvaluatorOutput)
modelReportGenerator = init_chat_model(model="openai:gpt-5-nano", temperature=0).with_structured_output(ReportGeneratorOutput)
modelNotifier = init_chat_model(model="openai:gpt-5-nano", temperature=0)

# Nodos del grafo
def nodeExtractor(state: State):
    """"""
    result = modelExtractor.invoke(
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

def nodeEvaluator(state: State):
    """"""
    result = modelEvaluator.invoke(
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

def nodeReportGenerator(state: State):
    """"""
    result = modelReportGenerator.invoke(
        [SystemMessage(content=REPORTGENERATOR)]
        + state["messages"]
        + [HumanMessage(content=f"""
            candidateName: {state["candidateName"]}
            candidateEmail: {state["candidateEmail"]}
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

def nodeNotifier(state: State):
    """"""
    result = modelNotifier.invoke(
        [SystemMessage(content=REPORTGENERATOR)]
        + state["messages"]
        + [HumanMessage(content=f"""
            candidateName: {state["candidateName"]}
            candidateEmail: {state["candidateEmail"]}
            score: {state["score"]}
            reportText: {state["reportText"]}
            recommendation: {state["recommendation"]}
        """)]
    )
    return {"messages": [result]}
