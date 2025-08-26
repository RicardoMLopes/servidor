from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from params.alerta import enviar_alerta
from typing import List
from database.dependencies import get_empresa_db
from model.schemas_cliente import ClienteCreate
from database.querys import ConsultaCliente, Insert_Cliente

import traceback

cliente_router = APIRouter()

@cliente_router.get("")
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