from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from params.alerta import enviar_alerta
from database.dependencies import get_empresa_db
from database.querys import ConsultaCondicoesPagamento, Insert_Condicao_Pagamento

import traceback

condicao_pagamento_router = APIRouter()

@condicao_pagamento_router.get("")
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
