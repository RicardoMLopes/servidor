from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_empresa_db
from querys import ConsultaParametro
import traceback
from typing import List


parameter_router = APIRouter()

@parameter_router.get("/")
async def listar_parameter(db: Session = Depends(get_empresa_db)):
    try:
        resultado = ConsultaParametro(db)

        if resultado:
            colunas = [
                "empresa", "vendedorPadrao", "atualizaCliente", "atualizaCondPagamento",
                "atualizaParametro", "atualizaProduto", "atualizaVendedor", "controlaSaldoEstoque",
                "casaDecimalQuantidade", "casaDecimalValor", "controlaFormaPagamento",
                "percentualDescontoVenda", "mostrarFinanceiro", "mostrarFinanceiroVencido",
                "dataUltimaAtualizacao", "situacaoRegistro", "dataRegistro", "versaoGeral",
                "versaoVendedor", "versaoCliente", "versaoCondicaoPagamento", "versaoCheckListPergunta",
                "versaoCheckListResposta", "versaoFinanceiro", "versaoRotaCondicaoPagamento",
                "versaoRotaCliente", "versaoProduto", "versaoParametro"
            ]

            dados = [dict(zip(colunas, item)) for item in resultado]
            return dados
        else:
            raise HTTPException(status_code=404, detail="Nenhum parametro encontrado.")

    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno: {e.__class__.__name__}: {str(e)}")