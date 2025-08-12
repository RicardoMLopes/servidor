from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from dependencies import get_empresa_db
from querys import ConsultaCondicoesPagamento

import traceback

condicao_pagamento_router = APIRouter()

@condicao_pagamento_router.get("/")
async def listar_condicoes_pagamento(db: Session = Depends(get_empresa_db)):
    try:
        resultado = ConsultaCondicoesPagamento(db)

        if resultado:
            colunas = [
                "empresa", "codigo", "descricao", "acrescimo", "desconto",
                "situacaoRegistro", "dataRegistro", "versao"
            ]
            dados = [dict(zip(colunas, item)) for item in resultado]
            return dados
        else:
            raise HTTPException(status_code=404, detail="Nenhuma condição de pagamento encontrada.")
    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno: {e.__class__.__name__}: {str(e)}")