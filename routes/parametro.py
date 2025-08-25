from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from params.alerta import enviar_alerta
from database.dependencies import get_empresa_db
from database.querys import ConsultaParametro, Insert_Parametro
import traceback

parameter_router = APIRouter()

@parameter_router.get("")
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

@parameter_router.post("/")
async def inserir_ou_atualizar_parametro(parametro: str, db: Session = Depends(get_empresa_db)):
    try:
        sucesso = Insert_Parametro(db, parametro)
        if not sucesso:
            raise HTTPException(status_code=400, detail="Erro ao inserir/atualizar parâmetro.")

        return {"mensagem": "Parâmetro inserido/atualizado com sucesso."}

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        enviar_alerta(assunto="Inserção de parâmetros", mensagem="Erro ao inserir/atualizar parâmetro: " + str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {e.__class__.__name__}: {str(e)}"
        )
