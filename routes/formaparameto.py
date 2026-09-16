import logging
from datetime import datetime
from typing import Optional, List
import pytz
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
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


class CondicaoPagamentoSchema(BaseModel):
    empresa: int
    codigo: str
    descricao: Optional[str] = None
    acrescimo: float = 0.0
    desconto: float = 0.0
    situacaoRegistro: Optional[str] = "I"
    dataRegistro: Optional[datetime] = None


@condicao_pagamento_router.post("/batch")
async def inserir_ou_atualizar_condicoes_pagamento_lote(
        condicoes: List[CondicaoPagamentoSchema],
        db=Depends(get_empresa_db)
):
    """
    Recebe uma lista de condições de pagamento enviadas via TJSONArray do Delphi
    e processa tudo em uma única transação no banco de dados.
    """
    if not condicoes:
        return {"mensagem": "Nenhum registro recebido para processamento.", "processados": 0}

    try:
        # Recomenda-se processar tudo dentro de uma transação (db.commit no final)
        total_processados = 0

        for condicao in condicoes:
            sucesso = Insert_Condicao_Pagamento(db, condicao)
            if not sucesso:
                raise Exception(f"Falha ao processar código: {condicao.codigo}")
            total_processados += 1

        # Confirma todas as inserções de uma vez só
        db.commit()

        return {
            "mensagem": "Condições de pagamento sincronizadas em lote com sucesso.",
            "total_processados": total_processados
        }

    except Exception as e:
        db.rollback()  # Desfaz as alterações caso ocorra algum erro no lote
        traceback.print_exc()
        enviar_alerta(
            assunto="Inserção em Lote de Condições de Pagamento",
            mensagem=f"Erro ao processar lote: {e.__class__.__name__}: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erro no lote: {e.__class__.__name__}: {str(e)}"
        )