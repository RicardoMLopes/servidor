from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_empresa_db
from querys import inserir_pedido  # função separada que faz a inserção
import traceback

pedido_router = APIRouter()

@pedido_router.post("")
async def inserir_pedido_api(nota: dict, db: Session = Depends(get_empresa_db)):
    """
    Rota para inserir um pedido no banco.
    Recebe o payload completo (movnota + itens) e chama a rotina `inserir_pedido`.
    """
    try:
        sucesso = inserir_pedido(db, nota)
        if sucesso:
            return {"status": "ok", "numerodocumento": nota.get("numerodocumento")}
        else:
            raise HTTPException(status_code=500, detail="Falha ao inserir pedido no banco.")
    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno: {e.__class__.__name__}: {str(e)}")
