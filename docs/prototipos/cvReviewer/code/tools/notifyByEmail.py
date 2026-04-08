# notifyByEmail.py
import time
from langchain_core.tools import tool

@tool
def notifyByEmail(email: str, subject: str, body: str) -> str:
    """Envía un correo electrónico al candidato. Usa esta herramienta cuando la puntuación del candidato sea superior a 8."""
    print(f"\n📧 Enviando correo a {email}...")
    time.sleep(2)
    print(f"✅ Correo enviado correctamente a {email}")
    return f"OK: correo enviado correctamente a {email}"