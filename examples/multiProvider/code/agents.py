# agents.py
from langchain_core.messages import SystemMessage, HumanMessage
from prompt import RESEARCHER, WRITER, CRITIC, EDITOR
from state import State
from langchain.chat_models import init_chat_model
from config import OLLAMA_BASE_URL
from pydantic import BaseModel, Field
# Importar herramientas (pendiente siguiente iteración)

# Salidas de los nodos 
class ResearcherOutput(BaseModel):
    research: str = Field(description="Notas de investigación recopiladas")

class WriterOutput(BaseModel):
    draft: str = Field(description="Borrador del artículo")

class CriticOutput(BaseModel):
    critique: str = Field(description="Crítica del borrador")

class EditorOutput(BaseModel):
    finalText: str = Field(description="Texto final revisado")

# Modelos
modelResearcher = init_chat_model(model="openai:gpt-5-mini", temperature=0).with_structured_output(ResearcherOutput)
modelWriter = init_chat_model(model="anthropic:claude-sonnet-4-6", temperature=0).with_structured_output(WriterOutput)
modelCritic = init_chat_model(model="google:gemini-2.5-flash", temperature=0).with_structured_output(CriticOutput)
modelEditor = init_chat_model(model="ollama:llama3.1", temperature=0, base_url=OLLAMA_BASE_URL).with_structured_output(EditorOutput)

# Nodos del grafo
def nodeResearcher(state: State):
    """"""
    result = modelResearcher.invoke(
        [SystemMessage(content=RESEARCHER)]
        + state["messages"]
        + [HumanMessage(content=f"""
            topic: {state["topic"]}
        """)]
    )
    return {
        "research": result.research
    }

def nodeWriter(state: State):
    """"""
    result = modelWriter.invoke(
        [SystemMessage(content=WRITER)]
        + state["messages"]
        + [HumanMessage(content=f"""
            topic: {state["topic"]}
            research: {state["research"]}
        """)]
    )
    return {
        "draft": result.draft
    }

def nodeCritic(state: State):
    """"""
    result = modelCritic.invoke(
        [SystemMessage(content=CRITIC)]
        + state["messages"]
        + [HumanMessage(content=f"""
            draft: {state["draft"]}
        """)]
    )
    return {
        "critique": result.critique
    }

def nodeEditor(state: State):
    """"""
    result = modelEditor.invoke(
        [SystemMessage(content=EDITOR)]
        + state["messages"]
        + [HumanMessage(content=f"""
            draft: {state["draft"]}
            critique: {state["critique"]}
        """)]
    )
    return {
        "finalText": result.finalText
    }
