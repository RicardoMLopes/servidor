from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import hashlib
import traceback
from datetime import datetime

from model.dictionary import criar_tabela_cadusers_se_nao_existir
from model.pedido import colunas_movnota, colunas_movnotaitem, pks_movnotaitem, pks_movnota
from database.dependencies import get_empresa_db
from database.querys import inserir_pedido  # função separada que faz a inserção
from params.alerta import enviar_alerta

pedido_router = APIRouter()

@pedido_router.post("")
async def inserir_pedido_api(nota: dict, db: Session = Depends(get_empresa_db)):
    # 🔹 Cria/atualiza tabelas se necessário
    criar_tabela_cadusers_se_nao_existir(db, "movnota", colunas_movnota, pks_movnota)
    criar_tabela_cadusers_se_nao_existir(db, "movnotaitem", colunas_movnotaitem, pks_movnotaitem)

    try:
        # 🔹 Gerar hash único do pedido
        hash_input = f"{nota.get('idpedido')}_{nota.get('codigovendedor')}_{nota.get('codigocliente')}_{nota.get('codigocondPagamento')}_{nota.get('empresa')}_{nota.get('valorTotal')}"
        pedido_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
        nota["pedido_hash"] = pedido_hash

        # 🔹 Verifica se já existe pedido com este hash
        pedido_existente = db.execute(
            text("SELECT numerodocumento FROM movnota WHERE pedido_hash = :pedido_hash"),
            {"pedido_hash": pedido_hash}
        ).mappings().fetchone()

        if pedido_existente:
            return {
                "status": "ok",
                "mensagem": "Pedido já registrado",
                "numerodocumento": pedido_existente["numerodocumento"]
            }

        # 🔹 Inserir pedido normalmente
        numerodocumento = inserir_pedido(db, nota)
        if numerodocumento:
            return {"status": "ok", "numerodocumento": numerodocumento}
        else:
            raise HTTPException(status_code=500, detail="Falha ao inserir pedido no banco.")

    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        enviar_alerta(
            assunto='Erro na sincronização do pedido',
            mensagem=f"Falha ao inserir pedido no banco: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {e.__class__.__name__}: {str(e)}"
        )
