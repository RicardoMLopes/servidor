from fastapi import APIRouter
from querys import ConsultaProduto
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_empresa_db
import traceback

products_router = APIRouter()


# requisição da lista de produtos
@products_router.get("/")
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