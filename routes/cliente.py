from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from params.alerta import enviar_alerta
from typing import List
from database.dependencies import get_empresa_db
from model.cliente.schemas_cliente import ClienteCreate
from database.querys import ConsultaCliente, Insert_Cliente
import time
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


@cliente_router.post("")
@cliente_router.post("/")
async def atualizar_clientes(clientes: List[ClienteCreate], db: Session = Depends(get_empresa_db)):
    """
    Insere ou atualiza a lista de clientes e devolve os totais detalhados do processamento.
    """
    qtd_total = len(clientes) if clientes else 0
    logging.info(f"📥 [API RECEBEU] Requisição POST /clientes/ com {qtd_total} cliente(s).")

    if qtd_total == 0:
        return {
            "mensagem": "Nenhum cliente fornecido.",
            "total_processado": 0,
            "tempo_execucao_segundos": 0
        }

    try:
        resultado = Insert_Cliente(db, clientes)

        if not resultado.get("sucesso"):
            raise HTTPException(
                status_code=400,
                detail="Erro ao inserir/atualizar a lista de clientes no banco de dados."
            )

        return {
            "mensagem": "Clientes sincronizados com sucesso.",
            "total_processado": resultado["total"],
            "tempo_execucao_segundos": resultado["tempo_execucao"]
        }

    except HTTPException:
        raise
    except Exception as e:
        mensagem_erro = f"Erro crítico na inserção/atualização de clientes: {str(e)}"
        logging.error(mensagem_erro, exc_info=True)
        enviar_alerta(assunto="Erro Crítico: Inserção de clientes", mensagem=mensagem_erro)
        raise HTTPException(status_code=500, detail=f"Erro interno: {e.__class__.__name__}: {str(e)}")