from fastapi import APIRouter
from querys import ConsultaEmpresa
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_empresa_db
import traceback

empresa_router = APIRouter()

# requisição do cadastro de empresa
@empresa_router.get("")
async def buscar_empresa(db: Session = Depends(get_empresa_db)):
    try:
        resultado = ConsultaEmpresa(db)
        if resultado:
            print(resultado)
            return {"codigo": resultado[0], "nome": resultado[1], "cnpj": resultado[2], "rua": resultado[3],
                    "numero": resultado[4], "bairro": resultado[5], "cidade": resultado[6], "telefone": resultado[7],
                    "email": resultado[8] }
        else:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")

    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno: {e.__class__.__name__}: {str(e)}")

