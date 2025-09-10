from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from params.alerta import enviar_alerta
from typing import List
from database.dependencies import get_empresa_db
from model.schemas_cliente import ClienteCreate
from database.querys import ConsultaCliente, Insert_Cliente
from datetime import datetime
from fastapi import Query
from typing import Optional
import pytz
import traceback

cliente_router = APIRouter()

@cliente_router.get("")
async def listar_clientes(
    last_sync: Optional[str] = Query(
        None,
        description="Data/hora da última sincronização no formato 'YYYY-MM-DD HH:MM:SS'"
    ),
    db: Session = Depends(get_empresa_db)
):
    try:
        filtro_data: Optional[str] = None
        if last_sync:
            try:
                # Valida formato igual ao usado em produtos
                datetime.strptime(last_sync, "%Y-%m-%d %H:%M:%S")
                filtro_data = last_sync
                logging.warning("📌 Filtro recebido em clientes: %s", filtro_data)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Formato inválido para last_sync. Use 'YYYY-MM-DD HH:MM:SS'"
                )

        # Consulta clientes
        dados = ConsultaCliente(db, filtro_data)

        # Hora atual no fuso de São Paulo
        tz_sp = pytz.timezone("America/Sao_Paulo")
        last_sync_servidor = datetime.now(tz_sp).strftime("%Y-%m-%d %H:%M:%S")

        return {
            "clientes": dados,
            "last_sync": last_sync_servidor
        }

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {e.__class__.__name__}: {str(e)}"
        )

@cliente_router.post("/")
async def atualizar_clientes(clientes: List[ClienteCreate], db: Session = Depends(get_empresa_db)):
    """
    Insere ou atualiza uma lista de clientes.
    Recebe JSON no body: [ {cliente1}, {cliente2}, ... ]
    """
    try:
        for cliente in clientes:
            sucesso = Insert_Cliente(db, cliente)
            if not sucesso:
                raise HTTPException(status_code=400, detail=f"Erro ao inserir/atualizar cliente {cliente.codigo}.")
        return {"mensagem": "Clientes inseridos/atualizados com sucesso."}
    except Exception as e:
        enviar_alerta(assunto="Inserção de clientes", mensagem="Erro ao inserir/atualizar clientes: " + str(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno: {e.__class__.__name__}: {str(e)}")