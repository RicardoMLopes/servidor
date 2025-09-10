import logging
from datetime import datetime
from typing import Optional

import pytz
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from params.alerta import enviar_alerta
from database.dependencies import get_empresa_db
from database.querys import ConsultaCondicoesPagamento, Insert_Condicao_Pagamento
from fastapi import Query
import traceback

condicao_pagamento_router = APIRouter()


@condicao_pagamento_router.get("")
async def listar_condicoes_pagamento(
        last_sync: Optional[str] = Query(None, description="Data/hora da última sincronização (ISO 8601)"),
        db: Session = Depends(get_empresa_db)
):
    try:
        logging.warning("DATA recebida do cliente: %s", last_sync)

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

        # 2️⃣ Consulta condições de pagamento
        resultado = ConsultaCondicoesPagamento(db, filtro_data)

        # 3️⃣ Converte cada Row do SQLAlchemy em dict
        dados = [dict(item) for item in resultado]

        # 4️⃣ Gera last_sync como string no formato desejado
        last_sync_servidor = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if dados else None

        # 5️⃣ Log antes de retornar
        logging.info("📦 last_sync enviado para o cliente: %s", last_sync_servidor)

        return {
            "condicoes": dados,
            "last_sync": last_sync_servidor
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {e.__class__.__name__}: {str(e)}"
        )


@condicao_pagamento_router.post("/")
async def inserir_ou_atualizar_condicao_pagamento(condicao: str, db: Session = Depends(get_empresa_db)):
    try:
        sucesso = Insert_Condicao_Pagamento(db, condicao)
        if not sucesso:
            raise HTTPException(status_code=400, detail="Erro ao inserir/atualizar condição de pagamento.")

        return {"mensagem": "Condição de pagamento inserida/atualizada com sucesso."}

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        enviar_alerta(assunto="Inserção de condições de pagamento", mensagem="Erro ao inserir/atualizar condição: " + str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {e.__class__.__name__}: {str(e)}"
        )
