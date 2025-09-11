from datetime import datetime
from typing import Optional

import pytz
from fastapi import Query

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from params.alerta import enviar_alerta
from database.dependencies import get_empresa_db
from database.querys import ConsultaVendedor, Insert_Vendedor
import traceback

vendedor_router = APIRouter()

# rota de listagem
@vendedor_router.get("")
async def listar_vendedores(
    last_sync: Optional[str] = Query(None, description="Data/hora da última sincronização (ISO 8601)"),
    db: Session = Depends(get_empresa_db)
):
    try:
        # 1️⃣ Converte last_sync recebido em datetime
        filtro_data: Optional[datetime] = None
        if last_sync:
            try:
                filtro_data = datetime.fromisoformat(last_sync)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Formato inválido de last_sync. Use ISO 8601 (ex: 2025-08-27T10:15:00)"
                )

        # 2️⃣ Consulta vendedores usando padrão ConsultaVendedor
        resultado = ConsultaVendedor(db, filtro_data)

        # 3️⃣ Converte cada Row em dict
        dados = [dict(item) for item in resultado]

        # 4️⃣ Define last_sync para o cliente como string "YYYY-MM-DD HH:mm:ss"
        last_sync_servidor = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("📅 last_sync enviado ao VENDEDOR:", last_sync_servidor)

        return {
            "vendedores": dados,
            "last_sync": last_sync_servidor
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {e.__class__.__name__}: {str(e)}"
        )




@vendedor_router.post("/")
async def atualizar_vendedor(vendedor: str, db: Session = Depends(get_empresa_db)):
    try:
        sucesso = Insert_Vendedor(db, vendedor)
        if not sucesso:
            raise HTTPException(status_code=400, detail="Erro ao inserir/atualizar vendedor.")

        return {"mensagem": "Vendedor inserido/atualizado com sucesso."}

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        enviar_alerta(assunto="Inserção de vendedores", mensagem="Erro ao inserir/atualizar vendedor: " + str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {e.__class__.__name__}: {str(e)}"
        )
