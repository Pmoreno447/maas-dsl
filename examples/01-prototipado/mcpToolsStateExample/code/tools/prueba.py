from langchain.tools import tool

@tool
def prueba(query: str) -> str:
    """Formatea el texto recibido como parametro

    Args:
        query: Texto a formatear
    """
    return query