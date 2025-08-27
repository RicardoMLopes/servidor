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
        filtro_data: Optional[datetime] = None
        if last_sync:
            try:
                filtro_data = datetime.fromisoformat(last_sync)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Formato inválido de last_sync. Use ISO 8601 (ex: 2025-08-27T10:15:00)"
                )

        resultado = ConsultaVendedor(db, filtro_data)

        colunas = [
            "empresa", "codigo", "codigorota", "nome",
            "situacaoRegistro", "dataRegistro", "versao"
        ]

        dados = []
        for item in resultado:
            if len(item) != len(colunas):
                dados.append({col: item[i] if i < len(item) else None for i, col in enumerate(colunas)})
            else:
                dados.append(dict(zip(colunas, item)))
        # Usa pytz para pegar hora de São Paulo
        tz_sp = pytz.timezone("America/Sao_Paulo")
        last_sync_servidor = datetime.now(tz_sp)
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
