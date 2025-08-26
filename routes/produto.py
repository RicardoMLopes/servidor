from fastapi import APIRouter
from params.alerta import enviar_alerta
from database.querys import ConsultaProduto, Insert_Produto
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from database.dependencies import get_empresa_db
import traceback

products_router = APIRouter()


# requisição da lista de produtos
@products_router.get("")
async def sincronizar_produto(db: Session = Depends(get_empresa_db)):
    try:
        resultado = ConsultaProduto(db)
        if resultado:
            colunas = ["empresa", "codigo", "descricao", "unidademedida", "codigobarra",
                       "agrupamento", "marca", "modelo", "tamanho", "cor", "peso",
                       "precoVenda", "casasdecimais", "percentualdesconto", "estoque", "reajustacondicaopagamento",
                       "percentualcomissao", "situacaoRegistro", "dataRegistro", "versao", "imagens"]

            dados = [dict(zip(colunas, item)) for item in resultado]

            return dados
        else:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno: {e.__class__.__name__}: {str(e)}")


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
