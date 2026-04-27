from langchain_core.tools import tool


@tool
def getInfoOrder(order_id: str) -> dict:
    """Devuelve toda la información existente sobre un pedido en el sistema."""
    return {
        "orderId": order_id,
        "orderStatus": "en tránsito",
        "productID": "PROD-78432",
        "productBatch": "LOTE-2024-B12",
        "trackingNumber": "TRK-00998877",
        "paymentAmount": 49,
        "paymentStatus": "pagado",
    }


@tool
def reopenShipmentCase(tracking_number: str) -> dict:
    """Dado el trackingNumber reabre el caso con la transportista."""
    return {
        "tracking_number": tracking_number,
        "status": "reopened",
        "message": f"El caso con la transportista para el envío {tracking_number} ha sido reabierto correctamente. Un agente de la transportista contactará en 24-48h.",
    }


@tool
def requestDuplicateShipment(order_id: str) -> dict:
    """Dado el orderId solicita el reenvío del pedido."""
    return {
        "order_id": order_id,
        "status": "requested",
        "new_tracking_number": "TRK-99112233",
        "message": f"Se ha solicitado el reenvío del pedido {order_id}. El nuevo número de seguimiento es TRK-99112233 y llegará en 3-5 días hábiles.",
    }


@tool
def requestRefund(order_id: str, payment_amount: int) -> dict:
    """Dado el orderId y paymentAmount tramita la devolución."""
    return {
        "order_id": order_id,
        "refund_amount": payment_amount,
        "status": "approved",
        "message": f"La devolución de {payment_amount}€ para el pedido {order_id} ha sido aprobada. El importe se abonará en 5-7 días hábiles.",
    }


@tool
def applyDiscount(order_id: str) -> dict:
    """Dado el orderId aplica un descuento como compensación."""
    return {
        "order_id": order_id,
        "discount_code": "COMP-15OFF",
        "discount_percentage": 15,
        "message": f"Se ha aplicado un descuento del 15% al pedido {order_id} como compensación. Código: COMP-15OFF.",
    }


@tool
def requestReplacement(order_id: str) -> dict:
    """Dado el orderId gestiona el envío de un producto de reemplazo."""
    return {
        "order_id": order_id,
        "status": "requested",
        "new_tracking_number": "TRK-55667788",
        "message": f"Se ha iniciado el envío de un producto de reemplazo para el pedido {order_id}. Número de seguimiento: TRK-55667788. Llegará en 2-4 días hábiles.",
    }


@tool
def requestReturn(order_id: str) -> dict:
    """Dado el orderId inicia la devolución de un producto y genera una etiqueta de devolución."""
    return {
        "order_id": order_id,
        "status": "initiated",
        "return_label": "LABEL-RTN-20458-PDF",
        "message": f"La devolución del pedido {order_id} ha sido iniciada. Se ha generado la etiqueta de devolución (LABEL-RTN-20458-PDF). Por favor, deposita el paquete en cualquier punto de recogida en los próximos 14 días.",
    }


@tool
def getDeliveryEstimate(order_id: str) -> dict:
    """Dado el orderId determina el tiempo que le queda al pedido para llegar."""
    return {
        "order_id": order_id,
        "estimated_days": 3,
        "estimated_date": "2026-04-30",
        "message": f"El pedido {order_id} tiene una entrega estimada para el 2026-04-30 (aproximadamente 3 días hábiles).",
    }
