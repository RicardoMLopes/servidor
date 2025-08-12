from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_empresa_db
from querys import ConsultaCliente

import traceback

cliente_router = APIRouter()

@cliente_router.get("/")
async def listar_clientes(db: Session = Depends(get_empresa_db)):
    try:
        resultado = ConsultaCliente(db)

        if resultado:
            colunas = [
                "empresa", "codigo", "codigovendedor", "nome", "contato", "cpfCnpj",
                "rua", "numero", "bairro", "cidade", "estado", "telefone",
                "limiteCredito", "observacao", "restricao", "reajuste",
                "situacaoRegistro", "dataRegistro", "versao"
            ]
            dados = [dict(zip(colunas, item)) for item in resultado]
            return dados
        else:
            raise HTTPException(status_code=404, detail="Nenhum cliente encontrado.")
    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno: {e.__class__.__name__}: {str(e)}")