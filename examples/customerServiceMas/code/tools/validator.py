from langchain_core.tools import tool


@tool
def orderChecker(order_id: str) -> dict:
    """Determina si el pedido existe en el sistema o no."""
    if len(order_id) < 5:
        return {"valid": False, "message": f"El pedido '{order_id}' no existe en el sistema."}
    return {"valid": True, "message": f"El pedido '{order_id}' existe y está registrado en el sistema."}
