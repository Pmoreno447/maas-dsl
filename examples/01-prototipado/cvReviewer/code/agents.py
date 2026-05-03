# agents.py
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from prompt import EXTRACTOR, EVALUATOR, REPORTGENERATOR, NOTIFIER
from state import State
from langchain.chat_models import init_chat_model


from pydantic import BaseModel, Field

from tools.Example import notifyByEmail

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
modelNotifier = init_chat_model(model="openai:gpt-5-nano", temperature=0).bind_tools([notifyByEmail])

_tools_by_name = {t.name: t for t in [notifyByEmail]}

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
            candidateName: {state.get("candidateName", "No registrado aún")}
            candidateEmail: {state.get("candidateEmail", "No registrado aún")}
            yearsExperience: {state.get("yearsExperience", "No registrado aún")}
            skills: {state.get("skills", "No registrado aún")}
            educationLevel: {state.get("educationLevel", "No registrado aún")}
            language: {state.get("language", "No registrado aún")}
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
            candidateName: {state.get("candidateName", "No registrado aún")}
            candidateEmail: {state.get("candidateEmail", "No registrado aún")}
            yearsExperience: {state.get("yearsExperience", "No registrado aún")}
            skills: {state.get("skills", "No registrado aún")}
            educationLevel: {state.get("educationLevel", "No registrado aún")}
            language: {state.get("language", "No registrado aún")}
            score: {state.get("score", "No registrado aún")}
            meetRequirement: {state.get("meetRequirement", "No registrado aún")}
            strengths: {state.get("strengths", "No registrado aún")}
            weaknesses: {state.get("weaknesses", "No registrado aún")}
        """)]
    )
    return {
        "reportText": result.reportText,
        "recommendation": result.recommendation
    }

async def nodeNotifier(state: State):
    """"""
    messages = (
        [SystemMessage(content=NOTIFIER)]
        + state["messages"]
        + [HumanMessage(content=f"""
            candidateName: {state.get("candidateName", "No registrado aún")}
            candidateEmail: {state.get("candidateEmail", "No registrado aún")}
            score: {state.get("score", "No registrado aún")}
            reportText: {state.get("reportText", "No registrado aún")}
            recommendation: {state.get("recommendation", "No registrado aún")}
        """)]
    )
    while True:
        response = await modelNotifier.ainvoke(messages)
        messages.append(response)
        if not response.tool_calls:
            return {"messages": [response]}
        for tc in response.tool_calls:
            tool = _tools_by_name[tc["name"]]
            try:
                result = await tool.ainvoke(tc["args"])
                messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
            except Exception as e:
                messages.append(ToolMessage(content=f"Error al llamar herramienta '{tc['name']}': {e}", tool_call_id=tc["id"]))
