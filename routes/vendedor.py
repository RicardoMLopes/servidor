from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from params.alerta import enviar_alerta
from database.dependencies import get_empresa_db
from database.querys import ConsultaVendedor, Insert_Vendedor
import traceback

vendedor_router = APIRouter()

@vendedor_router.get("")
async def listar_vendedores(db: Session = Depends(get_empresa_db)):
    try:
        resultado = ConsultaVendedor(db)

        if resultado:
            colunas = [
                "empresa", "codigo", "cd_rota", "nome",
                "situacaoRegistro", "dataRegistro", "versao"
            ]
            dados = [dict(zip(colunas, item)) for item in resultado]
            return dados
        else:
            raise HTTPException(status_code=404, detail="Nenhum vendedor encontrado.")
    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno: {e.__class__.__name__}: {str(e)}")


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
