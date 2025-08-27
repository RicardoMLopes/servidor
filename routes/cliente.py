from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
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
    last_sync: Optional[str] = Query(None, description="Data/hora da última sincronização (ISO 8601)"),
    db: Session = Depends(get_empresa_db)
):
    try:
        filtro_data: Optional[datetime] = None
        if last_sync:
            try:
                filtro_data = datetime.fromisoformat(last_sync)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Formato inválido de last_sync. Use ISO 8601 (ex: 2025-08-27T10:15:00)"
                )

        # Consulta clientes, filtrando por data se informado
        resultado = ConsultaCliente(db, filtro_data)

        if not resultado:
            return {"clientes": [], "last_sync": datetime.utcnow().isoformat()}

        colunas = [
            "empresa", "codigo", "codigovendedor", "nome", "contato", "cpfCnpj",
            "rua", "numero", "bairro", "cidade", "estado", "telefone",
            "limiteCredito", "observacao", "restricao", "reajuste",
            "situacaoRegistro", "dataRegistro", "versao"
        ]

        dados = []
        for item in resultado:
            if len(item) != len(colunas):
                # Preenche apenas os campos correspondentes se houver diferença
                dados.append({col: item[i] if i < len(item) else None for i, col in enumerate(colunas)})
            else:
                dados.append(dict(zip(colunas, item)))
        # Usa pytz para pegar hora de São Paulo
        tz_sp = pytz.timezone("America/Sao_Paulo")
        last_sync_servidor = datetime.now(tz_sp)
        return {
            "clientes": dados,
            "last_sync": last_sync_servidor
        }

    except HTTPException as e:
        raise e
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