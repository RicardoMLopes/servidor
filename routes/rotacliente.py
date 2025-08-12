from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from dependencies import get_empresa_db
from querys import ConsultaRotaCliente

import traceback

rota_cliente_router = APIRouter()

@rota_cliente_router.get("/")
async def listar_rotas_cliente(db: Session = Depends(get_empresa_db)):
    try:
        resultado = ConsultaRotaCliente(db)

        if resultado:
            colunas = [
                "empresa", "cd_rota", "cd_cliente", "situacaoRegistro",
                "dataRegistro", "versao"
            ]
            dados = [dict(zip(colunas, item)) for item in resultado]
            return dados
        else:
            raise HTTPException(status_code=404, detail="Nenhuma rota de cliente encontrada.")
    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno: {e.__class__.__name__}: {str(e)}")