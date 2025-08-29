import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from params.alerta import enviar_alerta  # sua função Python

email_router = APIRouter()

# Modelo do payload esperado
class EmailRequest(BaseModel):
    assunto: str
    mensagem: str
    jsonData: Optional[dict] = None
    to: Optional[List[str]] = None  # lista de destinatários opcional

@email_router.post("/")
async def enviar_alerta_endpoint(payload: EmailRequest):
    logging.warning("Resultado do email: ",payload)
    try:
        # Monta a mensagem final
        mensagem_final = payload.mensagem
        if payload.jsonData:
            mensagem_final += "\n\nDados adicionais:\n" + str(payload.jsonData)

        # Chama sua função de envio
        enviar_alerta(payload.assunto, mensagem_final, to=payload.to)

        return {"success": True}
    except Exception as e:
        print(f"❌ Erro ao processar /enviar-alerta: {e}")
        raise HTTPException(status_code=500, detail=str(e))
