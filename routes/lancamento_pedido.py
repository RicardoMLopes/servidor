from io import BytesIO
import logging
import os
import pdfkit
from fastapi import APIRouter, Depends, Form, Request, status
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session
from sqlalchemy import text
import hashlib
import traceback
import tempfile
from fastapi import Query
from datetime import datetime, date
from starlette.responses import StreamingResponse, JSONResponse
from database.connection import get_empresa_session, DB_CHAVE
from function.funtions import gerar_token_cnpj, moeda_br
from database.dependencies import get_empresa_db, get_nome_banco_por_token
from database.querys import inserir_pedido, ConsultaEmpresa, ConsultaVendedor, \
    Consultar_vendedor_user, ConsultaVendedores, ConsultaEmpresaPorCNPJ  # função separada que faz a inserção
from params.alerta import enviar_alerta
from typing import Optional
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import shutil
from decimal import Decimal
from dateutil.parser import parse
from fastapi import Query, HTTPException
from sqlalchemy.sql import text

mov_pedido_router = APIRouter()

templates = Jinja2Templates(directory="templates")
templates.env.globals['now'] = datetime.now


@mov_pedido_router.get("/novo", response_class=HTMLResponse)
async def tela_novo_pedido(request: Request, token: Optional[str] = Query(None)):
    if not token:
        raise HTTPException(status_code=400, detail="Token da empresa não fornecido.")

    # 1. Descobre o nome do banco a partir do token
    nome_banco = get_nome_banco_por_token(token)
    if not nome_banco:
        raise HTTPException(status_code=403, detail="Token inválido ou empresa não encontrada")

    session_empresa = get_empresa_session(nome_banco)

    codigo_vendedor = None
    codigo_empresa = 1  # Valor padrão caso não encontre na tabela

    with session_empresa as db:
        # Exemplo: Se você tiver o usuário na sessão/request, substitua 'usuario_atual' pela forma que pega o user logado
        # Ex: usuario_logado = request.state.user (ajuste conforme a autenticação do seu projeto)
        usuario_logado = getattr(request.state, "user", None) or "admin" # Ajuste conforme sua auth

        # 🔹 Tenta buscar o vendedor na tabela de usuários (cadusers)

        user_query = db.execute(
            text("SELECT codigovendedor, empresa FROM cadusers WHERE usuario = :usuario AND situacaoregistro<> 'E' "),
            {"usuario": usuario_logado}
        ).fetchone()

        if user_query and user_query._mapping.get("codigovendedor"):
            codigo_vendedor = str(user_query._mapping["codigovendedor"]).strip()
            if user_query._mapping.get("empresa"):
                codigo_empresa = int(user_query._mapping["empresa"])

        # 🔹 Se não encontrou no usuário, busca o vendedor padrão no parâmetro (cadparametro)
        if not codigo_vendedor:
            param_query = db.execute(
                text("SELECT vendedorpadrao, empresa FROM cadparametro LIMIT 1")
            ).fetchone()

            if param_query:
                codigo_vendedor = str(param_query._mapping.get("vendedorpadrao", "001")).strip()
                if param_query._mapping.get("empresa"):
                    codigo_empresa = int(param_query._mapping["empresa"])

        # Fallback de segurança definitivo se nada for encontrado
        if not codigo_vendedor:
            codigo_vendedor = "001"

    # Passa esses valores via contexto para o template HTML preencher os inputs ocultos
    return templates.TemplateResponse(
        "pedido/movimento/lancamento_pedido.html",
        {
            "request": request,
            "token": token,
            "codigo_vendedor": codigo_vendedor,
            "empresa": codigo_empresa
        }
    )

@mov_pedido_router.post("", status_code=status.HTTP_201_CREATED)
async def inserir_pedido_api(pedido_data: dict, db: Session = Depends(get_empresa_db)):
    try:
        nota = pedido_data

        # 🔹 Gerar hash único do pedido (idempotência)
        hash_input = f"{nota.get('idpedido')}_{nota.get('codigovendedor')}_{nota.get('codigocliente')}_{nota.get('codigocondPagamento')}_{nota.get('empresa')}_{nota.get('valorTotal')}"
        pedido_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
        nota["pedido_hash"] = pedido_hash

        # 🔹 Verifica se já existe pedido com este hash no banco
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

        # 🔹 Inserir pedido utilizando a função do seu módulo de queries
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


@mov_pedido_router.get("/buscar-produtos")
async def buscar_produtos(token: str = Query(...), termo: Optional[str] = Query(None)):
    nome_banco = get_nome_banco_por_token(token)
    if not nome_banco:
        raise HTTPException(status_code=403, detail="Token inválido")

    session_empresa = get_empresa_session(nome_banco)
    with session_empresa as db:
        sql = """
            SELECT codigo, codigobarra, descricao, precoVenda 
            from cadproduto 
            where situacaoRegistro <> 'E'
        """
        params = {}

        if termo and termo.strip():
            sql += " AND (codigo = :termo OR codigobarra = :termo OR descricao LIKE :termo_like)"
            params["termo"] = termo.strip()
            params["termo_like"] = f"%{termo.strip()}%"

        sql += " LIMIT 50"  # Limita para não pesar a resposta

        resultados = db.execute(text(sql), params).fetchall()

        produtos = [
            {
                "codigo": p._mapping["codigo"],
                "codigobarra": p._mapping.get("codigobarra"),
                "descricao": p._mapping["descricao"],
                "precoVenda": float(p._mapping.get("precoVenda") or 0)
            }
            for p in resultados
        ]
        return {"produtos": produtos}


@mov_pedido_router.get("/buscar-clientes")
async def buscar_clientes(token: str = Query(...), termo: Optional[str] = Query(None)):
    nome_banco = get_nome_banco_por_token(token)
    if not nome_banco:
        raise HTTPException(status_code=403, detail="Token inválido")

    session_empresa = get_empresa_session(nome_banco)
    with session_empresa as db:
        sql = """
            SELECT codigo, nome, cpfcnpj 
            from cadcliente 
            where situacaoRegistro <> 'E'
        """
        params = {}

        if termo and termo.strip():
            sql += " AND (codigo = :termo OR nome LIKE :termo_like OR cpfcnpj LIKE :termo_like)"
            params["termo"] = termo.strip()
            params["termo_like"] = f"%{termo.strip()}%"

        sql += " LIMIT 50"

        resultados = db.execute(text(sql), params).fetchall()

        clientes = [
            {
                "codigo": c._mapping["codigo"],
                "nome": c._mapping["nome"],
                "cpfcnpj": c._mapping.get("cpfcnpj") or ""
            }
            for c in resultados
        ]
        return {"clientes": clientes}