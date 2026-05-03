# agents.py
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from prompt import VALIDATOR, INFOEXTRACTOR, ANSWERWRITER, SHIPPINGHELPER, PAYMENTHELPER, PRODUCTHELPER, GENERALHELPER, PROBLEMORCHESTRATOR
from state import State
from langchain.chat_models import init_chat_model

from pydantic import BaseModel, Field

from tools.validator import orderChecker
from tools.Order import getInfoOrder
from tools.Order import reopenShipmentCase
from tools.Order import requestDuplicateShipment
from tools.Order import requestRefund
from tools.Order import applyDiscount
from tools.Order import requestReplacement
from tools.Order import requestReturn
from tools.Order import getDeliveryEstimate

# Salidas de los nodos
class ValidatorOutput(BaseModel):
    """Llama a esta herramienta cuando hayas terminado para entregar el resultado final."""
    isValid: bool = Field(description="Si el mensaje del cliente es real(es en serio y no te está tomando el pelo) y válido (el id del pedido existe) será True, en caso contrario False.")

class InfoExtractorOutput(BaseModel):
    """Llama a esta herramienta cuando hayas terminado para entregar el resultado final."""
    orderId: str = Field(description="Id del pedido con un problema")
    issueDescription: str = Field(description="Descripción del problema")
    preferredSolution: str = Field(description="Solución que ha pedido el cliente preferentemente si es que ha pedido alguna.")
    orderStatus: str = Field(description="Estado del pedido (entregado, procesando, en transito...)")
    productID: str = Field(description="Id del producto con problemas")
    productBatch: str = Field(description="Id del lote del producto con problemas")
    trackingNumber: str = Field(description="Numero de seguimiento del mensajero")
    paymentAmount: int = Field(description="Precio del producto.")
    paymentStatus: str = Field(description="Estado del pago")

class ShippingHelperOutput(BaseModel):
    """Llama a esta herramienta cuando hayas terminado para entregar el resultado final."""
    decision: str = Field(description="Decisión tomada para resolver el pedido")

class PaymentHelperOutput(BaseModel):
    """Llama a esta herramienta cuando hayas terminado para entregar el resultado final."""
    decision: str = Field(description="Decisión tomada para resolver el pedido")

class ProductHelperOutput(BaseModel):
    """Llama a esta herramienta cuando hayas terminado para entregar el resultado final."""
    decision: str = Field(description="Decisión tomada para resolver el pedido")

class GeneralHelperOutput(BaseModel):
    """Llama a esta herramienta cuando hayas terminado para entregar el resultado final."""
    decision: str = Field(description="Decisión tomada para resolver el pedido")

# Modelos
modelValidator = init_chat_model(model="openai:gpt-5-nano", temperature=0).bind_tools([orderChecker, ValidatorOutput], tool_choice="required")
modelInfoExtractor = init_chat_model(model="openai:gpt-5-nano", temperature=0).bind_tools([getInfoOrder, InfoExtractorOutput], tool_choice="required")
modelAnswerWriter = init_chat_model(model="openai:gpt-5-nano", temperature=0)
modelShippingHelper = init_chat_model(model="openai:gpt-5-nano", temperature=0).bind_tools([reopenShipmentCase, requestDuplicateShipment, ShippingHelperOutput], tool_choice="required")
modelPaymentHelper = init_chat_model(model="openai:gpt-5-nano", temperature=0).bind_tools([requestRefund, applyDiscount, PaymentHelperOutput], tool_choice="required")
modelProductHelper = init_chat_model(model="openai:gpt-5-nano", temperature=0).bind_tools([requestReplacement, requestReturn, getDeliveryEstimate, ProductHelperOutput], tool_choice="required")
modelGeneralHelper = init_chat_model(model="openai:gpt-5-nano", temperature=0).bind_tools([getDeliveryEstimate, GeneralHelperOutput], tool_choice="required")

_tools_by_name = {t.name: t for t in [orderChecker, getInfoOrder, reopenShipmentCase, requestDuplicateShipment, requestRefund, applyDiscount, requestReplacement, requestReturn, getDeliveryEstimate]}

# Nodos del grafo
async def nodeValidator(state: State):
    """Agente encargado de validar el mensaje del cliente."""
    messages = (
        [SystemMessage(content=VALIDATOR)]
        + state["messages"]
        
    )
    while True:
        response = await modelValidator.ainvoke(messages)
        messages.append(response)
        if not response.tool_calls:
            return {"messages": [response]}
        for tc in response.tool_calls:
            if tc["name"] == "ValidatorOutput":
                return {
                    "isValid": tc["args"]["isValid"]
                }
        for tc in response.tool_calls:
            tool = _tools_by_name[tc["name"]]
            try:
                result = await tool.ainvoke(tc["args"])
                messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
            except Exception as e:
                messages.append(ToolMessage(content=f"Error al llamar herramienta '{tc['name']}': {e}", tool_call_id=tc["id"]))

async def nodeInfoExtractor(state: State):
    """Agente encargado de rellenar el estado con la información del pedido"""
    messages = (
        [SystemMessage(content=INFOEXTRACTOR)]
        + state["messages"]
        
    )
    while True:
        response = await modelInfoExtractor.ainvoke(messages)
        messages.append(response)
        if not response.tool_calls:
            return {"messages": [response]}
        for tc in response.tool_calls:
            if tc["name"] == "InfoExtractorOutput":
                return {
                    "orderId": tc["args"]["orderId"],
                    "issueDescription": tc["args"]["issueDescription"],
                    "preferredSolution": tc["args"]["preferredSolution"],
                    "orderStatus": tc["args"]["orderStatus"],
                    "productID": tc["args"]["productID"],
                    "productBatch": tc["args"]["productBatch"],
                    "trackingNumber": tc["args"]["trackingNumber"],
                    "paymentAmount": tc["args"]["paymentAmount"],
                    "paymentStatus": tc["args"]["paymentStatus"]
                }
        for tc in response.tool_calls:
            tool = _tools_by_name[tc["name"]]
            try:
                result = await tool.ainvoke(tc["args"])
                messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
            except Exception as e:
                messages.append(ToolMessage(content=f"Error al llamar herramienta '{tc['name']}': {e}", tool_call_id=tc["id"]))

def nodeAnswerWriter(state: State):
    """Agente encargado de responder al usuario"""
    result = modelAnswerWriter.invoke(
        [SystemMessage(content=ANSWERWRITER)]
        + state["messages"]
        + [HumanMessage(content=f"""
            isValid: {state.get("isValid", "No registrado aún")}
            decision: {state.get("decision", "No registrado aún")}
        """)]
    )
    return {"messages": [result]}

async def nodeShippingHelper(state: State):
    """Especialista en problemas de envios."""
    messages = (
        [SystemMessage(content=SHIPPINGHELPER)]
        + state["messages"]
        + [HumanMessage(content=f"""
            orderId: {state.get("orderId", "No registrado aún")}
            issueDescription: {state.get("issueDescription", "No registrado aún")}
            preferredSolution: {state.get("preferredSolution", "No registrado aún")}
            orderStatus: {state.get("orderStatus", "No registrado aún")}
            productID: {state.get("productID", "No registrado aún")}
            productBatch: {state.get("productBatch", "No registrado aún")}
            trackingNumber: {state.get("trackingNumber", "No registrado aún")}
            paymentAmount: {state.get("paymentAmount", "No registrado aún")}
            paymentStatus: {state.get("paymentStatus", "No registrado aún")}
        """)]
    )
    while True:
        response = await modelShippingHelper.ainvoke(messages)
        messages.append(response)
        if not response.tool_calls:
            return {"messages": [response]}
        for tc in response.tool_calls:
            if tc["name"] == "ShippingHelperOutput":
                return {
                    "decision": tc["args"]["decision"]
                }
        for tc in response.tool_calls:
            tool = _tools_by_name[tc["name"]]
            try:
                result = await tool.ainvoke(tc["args"])
                messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
            except Exception as e:
                messages.append(ToolMessage(content=f"Error al llamar herramienta '{tc['name']}': {e}", tool_call_id=tc["id"]))

async def nodePaymentHelper(state: State):
    """Especialista en problemas de pago."""
    messages = (
        [SystemMessage(content=PAYMENTHELPER)]
        + state["messages"]
        + [HumanMessage(content=f"""
            orderId: {state.get("orderId", "No registrado aún")}
            issueDescription: {state.get("issueDescription", "No registrado aún")}
            preferredSolution: {state.get("preferredSolution", "No registrado aún")}
            orderStatus: {state.get("orderStatus", "No registrado aún")}
            productID: {state.get("productID", "No registrado aún")}
            productBatch: {state.get("productBatch", "No registrado aún")}
            trackingNumber: {state.get("trackingNumber", "No registrado aún")}
            paymentAmount: {state.get("paymentAmount", "No registrado aún")}
            paymentStatus: {state.get("paymentStatus", "No registrado aún")}
        """)]
    )
    while True:
        response = await modelPaymentHelper.ainvoke(messages)
        messages.append(response)
        if not response.tool_calls:
            return {"messages": [response]}
        for tc in response.tool_calls:
            if tc["name"] == "PaymentHelperOutput":
                return {
                    "decision": tc["args"]["decision"]
                }
        for tc in response.tool_calls:
            tool = _tools_by_name[tc["name"]]
            try:
                result = await tool.ainvoke(tc["args"])
                messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
            except Exception as e:
                messages.append(ToolMessage(content=f"Error al llamar herramienta '{tc['name']}': {e}", tool_call_id=tc["id"]))

async def nodeProductHelper(state: State):
    """Especialista en problemas de envios."""
    messages = (
        [SystemMessage(content=PRODUCTHELPER)]
        + state["messages"]
        + [HumanMessage(content=f"""
            orderId: {state.get("orderId", "No registrado aún")}
            issueDescription: {state.get("issueDescription", "No registrado aún")}
            preferredSolution: {state.get("preferredSolution", "No registrado aún")}
            orderStatus: {state.get("orderStatus", "No registrado aún")}
            productID: {state.get("productID", "No registrado aún")}
            productBatch: {state.get("productBatch", "No registrado aún")}
            trackingNumber: {state.get("trackingNumber", "No registrado aún")}
            paymentAmount: {state.get("paymentAmount", "No registrado aún")}
            paymentStatus: {state.get("paymentStatus", "No registrado aún")}
        """)]
    )
    while True:
        response = await modelProductHelper.ainvoke(messages)
        messages.append(response)
        if not response.tool_calls:
            return {"messages": [response]}
        for tc in response.tool_calls:
            if tc["name"] == "ProductHelperOutput":
                return {
                    "decision": tc["args"]["decision"]
                }
        for tc in response.tool_calls:
            tool = _tools_by_name[tc["name"]]
            try:
                result = await tool.ainvoke(tc["args"])
                messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
            except Exception as e:
                messages.append(ToolMessage(content=f"Error al llamar herramienta '{tc['name']}': {e}", tool_call_id=tc["id"]))

async def nodeGeneralHelper(state: State):
    """Especialista en problemas generales."""
    messages = (
        [SystemMessage(content=GENERALHELPER)]
        + state["messages"]
        + [HumanMessage(content=f"""
            orderId: {state.get("orderId", "No registrado aún")}
            issueDescription: {state.get("issueDescription", "No registrado aún")}
            preferredSolution: {state.get("preferredSolution", "No registrado aún")}
            orderStatus: {state.get("orderStatus", "No registrado aún")}
            productID: {state.get("productID", "No registrado aún")}
            productBatch: {state.get("productBatch", "No registrado aún")}
            trackingNumber: {state.get("trackingNumber", "No registrado aún")}
            paymentAmount: {state.get("paymentAmount", "No registrado aún")}
            paymentStatus: {state.get("paymentStatus", "No registrado aún")}
        """)]
    )
    while True:
        response = await modelGeneralHelper.ainvoke(messages)
        messages.append(response)
        if not response.tool_calls:
            return {"messages": [response]}
        for tc in response.tool_calls:
            if tc["name"] == "GeneralHelperOutput":
                return {
                    "decision": tc["args"]["decision"]
                }
        for tc in response.tool_calls:
            tool = _tools_by_name[tc["name"]]
            try:
                result = await tool.ainvoke(tc["args"])
                messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
            except Exception as e:
                messages.append(ToolMessage(content=f"Error al llamar herramienta '{tc['name']}': {e}", tool_call_id=tc["id"]))
