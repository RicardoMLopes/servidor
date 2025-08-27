from datetime import datetime
from typing import Optional
import pytz
from fastapi import APIRouter
from fastapi import Query

from params.alerta import enviar_alerta
from database.querys import ConsultaProduto, Insert_Produto
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from database.dependencies import get_empresa_db
import traceback

products_router = APIRouter()


@products_router.get("")
async def listar_produtos(
    last_sync: Optional[str] = Query(
        None,
        description="Data/hora da última sincronização (ISO 8601)"
    ),
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

        # Consulta produtos no banco, filtrando por data se last_sync informado
        resultado = ConsultaProduto(db, filtro_data)

        # Define as colunas do retorno
        colunas = [
            "empresa", "codigo", "descricao", "unidadeMedida", "codigobarra",
            "agrupamento", "marca", "modelo", "tamanho", "cor", "peso",
            "precovenda", "casasdecimais", "percentualdesconto", "estoque",
            "reajustacondicaopagamento", "percentualComissao", "situacaoregistro",
            "dataRegistro", "versao", "imagens"
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
            "produtos": dados,
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


@products_router.post("/")
async def atualizar_produto(produto: str, db: Session = Depends(get_empresa_db)):
    try:
        sucesso = Insert_Produto(db, produto)
        if not sucesso:
            raise HTTPException(status_code=400, detail="Erro ao inserir/atualizar produto.")

        return {"mensagem": "Produto inserido/atualizado com sucesso."}

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        enviar_alerta(assunto="Inserção de produtos", mensagem="Erro ao inserir/atualizar produto: " + str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {e.__class__.__name__}: {str(e)}"
        )
