from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from dependencies import get_empresa_db
from querys import ConsultaVendedor
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