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
from fastapi import Query, HTTPException
from sqlalchemy.sql import text
mov_pedido_router = APIRouter()

templates = Jinja2Templates(directory="templates")
templates.env.globals['now'] = datetime.now

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo


@mov_pedido_router.get("/novo", response_class=HTMLResponse)
async def tela_novo_pedido(request: Request, token: Optional[str] = Query(None)):
    if not token:
        raise HTTPException(status_code=400, detail="Token da empresa não fornecido.")

    nome_banco = get_nome_banco_por_token(token)
    if not nome_banco:
        raise HTTPException(status_code=403, detail="Token inválido ou empresa não encontrada")

    session_empresa = get_empresa_session(nome_banco)

    codigo_vendedor = "001"
    codigo_empresa = 1
    codigo_cliente_padrao = ""
    nome_cliente_padrao = "Nenhum cliente selecionado"
    doc_cliente_padrao = "—"
    codigo_cond_pagamento_padrao = "001"

    with session_empresa as db:
        usuario_logado = getattr(request.state, "user", None) or "admin"

        # 1. Busca o vendedor do usuário logado ou o padrão do parâmetro
        user_query = db.execute(
            text("SELECT codigovendedor, empresa FROM cadusers WHERE usuario = :usuario AND situacaoregistro <> 'E'"),
            {"usuario": usuario_logado}
        ).fetchone()

        if user_query and user_query._mapping.get("codigovendedor"):
            codigo_vendedor = str(user_query._mapping["codigovendedor"]).strip()
            if user_query._mapping.get("empresa"):
                codigo_empresa = int(user_query._mapping["empresa"])

        # 2. Busca os dados da tabela cadparametro (clientepadrao, vendedorpadrao, condicaopagamentopadrao)
        param_query = db.execute(
            text("SELECT vendedorpadrao, clientepadrao, condicaopagamentopadrao, empresa FROM cadparametro LIMIT 1")
        ).fetchone()

        if param_query:
            if not codigo_vendedor and param_query._mapping.get("vendedorpadrao"):
                codigo_vendedor = str(param_query._mapping["vendedorpadrao"]).strip()

            if param_query._mapping.get("empresa"):
                codigo_empresa = int(param_query._mapping["empresa"])

            if param_query._mapping.get("condicaopagamentopadrao"):
                codigo_cond_pagamento_padrao = str(param_query._mapping["condicaopagamentopadrao"]).strip()

            # Busca o cliente padrão configurado no parâmetro
            cod_cliente_param = param_query._mapping.get("clientepadrao")
            if cod_cliente_param:
                cliente_query = db.execute(
                    text(
                        "SELECT codigo, nome, cpfcnpj FROM cadcliente WHERE codigo = :codigo AND situacaoregistro <> 'E' LIMIT 1"),
                    {"codigo": str(cod_cliente_param).strip()}
                ).fetchone()

                if cliente_query:
                    codigo_cliente_padrao = str(cliente_query._mapping.get("codigo", "")).strip()
                    nome_cliente_padrao = str(cliente_query._mapping.get("nome", "Cliente Sem Nome")).strip()
                    doc_cliente_padrao = str(cliente_query._mapping.get("cpfcnpj", "—")).strip()

    # Retorna a tela limpa alimentada com os padrões do sistema
    return templates.TemplateResponse(
        "pedido/movimento/lancamento_pedido.html",
        {
            "request": request,
            "token": token,
            "codigo_vendedor": codigo_vendedor,
            "empresa": codigo_empresa,
            "codigo_cliente_padrao": codigo_cliente_padrao,
            "nome_cliente_padrao": nome_cliente_padrao,
            "doc_cliente_padrao": doc_cliente_padrao,
            "codigo_cond_pagamento_padrao": codigo_cond_pagamento_padrao,
            "pedido_existente": None,  # Começa sempre null no clique de Novo
            "itens_pedido": [],
            "totais_pedido": {"bruto": 0, "desconto": 0, "acrescimo": 0, "liquido": 0}
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
            FROM cadcliente 
            WHERE situacaoRegistro <> 'E'
        """
        params = {}

        if termo and termo.strip():
            termo_limpo = termo.strip()
            if termo_limpo.isdigit():
                sql += " AND (codigo = :termo OR cpfcnpj LIKE :termo_like)"
                params["termo"] = termo_limpo
                params["termo_like"] = f"%{termo_limpo}%"
            else:
                sql += " AND nome LIKE :termo_like"
                params["termo_like"] = f"%{termo_limpo}%"

        sql += " ORDER BY nome LIMIT 15"

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


@mov_pedido_router.post("/adicionar-item")
async def adicionar_item_pedido(dados: dict, token: str = Query(...)):
    nome_banco = get_nome_banco_por_token(token)
    if not nome_banco:
        raise HTTPException(status_code=403, detail="Token inválido")

    session_empresa = get_empresa_session(nome_banco)
    with session_empresa as db:
        try:
            empresa = dados.get("empresa", 1)
            numerodocumento = dados.get("numerodocumento")
            codigovendedor = dados.get("codigovendedor")
            codigocliente = dados.get("codigocliente")
            codigocondPagamento = dados.get("codigocondPagamento")
            idpedido = dados.get("idpedido")

            item = dados.get("item")
            quantidade = float(item.get("quantidade", 0))
            valor_unitario = float(item.get("valorUnitario", 0))
            total_item = quantidade * valor_unitario

            try:
                data_atual = datetime.now(ZoneInfo("America/Sao_Paulo"))
            except Exception:
                data_atual = datetime.now()
            data_formatada = data_atual.strftime("%Y-%m-%d %H:%M:%S")

            # 🔹 Busca o nome correto do cliente direto na tabela cadcliente para garantir integridade
            nome_cliente = dados.get("nomecliente")
            if codigocliente:
                cli_query = db.execute(
                    text("SELECT nome FROM cadcliente WHERE codigo = :codigo AND situacaoregistro <> 'E' LIMIT 1"),
                    {"codigo": str(codigocliente).strip()}
                ).fetchone()
                if cli_query and cli_query._mapping.get("nome"):
                    nome_cliente = cli_query._mapping["nome"]

            # 🔹 Se não veio numerodocumento, é o primeiro item: gera o próximo número
            if not numerodocumento:
                result_prox = db.execute(
                    text("SELECT COALESCE(MAX(numerodocumento),0)+1 AS prox FROM movnota WHERE empresa=:empresa"),
                    {"empresa": empresa}
                ).mappings().fetchone()
                numerodocumento = result_prox["prox"] if result_prox else 1

            if not idpedido:
                idpedido = numerodocumento

            # 🔹 Valida se a MovNota já existe gravada no banco
            sql_busca_nota = text("""
                SELECT valorTotal FROM movnota 
                WHERE empresa = :empresa AND numerodocumento = :numerodocumento
                LIMIT 1
            """)

            resultado_nota = db.execute(sql_busca_nota, {
                "empresa": empresa,
                "numerodocumento": numerodocumento
            }).mappings().fetchone()

            if not resultado_nota:
                # 📌 1ª VEZ: Grava o Cabeçalho (MovNota)
                sql_insert_nota = text("""
                    INSERT INTO movnota
                    (empresa, numerodocumento, codigocondPagamento, codigovendedor, codigocliente,
                     nomecliente, idpedido, valorDesconto, valorDespesas, valorFrete,
                     valorTotal, pesoTotal, observacao, status, dataLancamento, situacaoRegistro, dataRegistro, pedido_hash)
                    VALUES
                    (:empresa, :numerodocumento, :codigocondPagamento, :codigovendedor, :codigocliente,
                     :nomecliente, :idpedido, :valorDesconto, :valorDespesas, :valorFrete,
                     :valorTotal, :pesoTotal, :observacao, :status, :dataLancamento, :situacaoRegistro, :dataRegistro, :pedido_hash)
                """)

                db.execute(sql_insert_nota, {
                    "empresa": empresa,
                    "numerodocumento": numerodocumento,
                    "codigocondPagamento": codigocondPagamento,
                    "codigovendedor": codigovendedor,
                    "codigocliente": codigocliente,
                    "nomecliente": nome_cliente,
                    "idpedido": idpedido,
                    "valorDesconto": dados.get("valorDesconto", 0),
                    "valorDespesas": dados.get("valorDespesas", 0),
                    "valorFrete": dados.get("valorFrete", 0),
                    "valorTotal": total_item,
                    "pesoTotal": dados.get("pesoTotal", 0),
                    "observacao": dados.get("observacao", ""),
                    "status": dados.get("status", "P"),
                    "dataLancamento": dados.get("dataLancamento"),
                    "situacaoRegistro": dados.get("situacaoRegistro", "I"),
                    "dataRegistro": data_formatada,
                    "pedido_hash": dados.get("pedido_hash")
                })
            else:
                # 📌 A MOVNOTA JÁ EXISTE: Atualiza o valor total E sincroniza o cliente/vendedor/condpagto caso tenham mudado
                novo_valor_total = float(resultado_nota["valorTotal"]) + total_item

                sql_update_nota = text("""
                    UPDATE movnota 
                    SET valorTotal = :novo_valor_total,
                        codigocliente = :codigocliente,
                        nomecliente = :nomecliente,
                        codigovendedor = :codigovendedor,
                        codigocondPagamento = :codigocondPagamento
                    WHERE empresa = :empresa AND numerodocumento = :numerodocumento
                """)
                db.execute(sql_update_nota, {
                    "novo_valor_total": novo_valor_total,
                    "codigocliente": codigocliente,
                    "nomecliente": nome_cliente,
                    "codigovendedor": codigovendedor,
                    "codigocondPagamento": codigocondPagamento,
                    "empresa": empresa,
                    "numerodocumento": numerodocumento
                })

            # 🔹 Grava o item na tabela movnotaitem
            sql_insert_item = text("""
                INSERT INTO movnotaitem
                (empresa, numerodocumento, codigovendedor, codigoproduto, idpedido, descricaoproduto,
                 valorUnitario, valorunitariovenda, valorDesconto, valoracrescimo, valorTotal,
                 quantidade, codigocliente, dataRegistro, situacaoRegistro, movnota_id)
                VALUES
                (:empresa, :numerodocumento, :codigovendedor, :codigoproduto, :idpedido, :descricaoproduto,
                 :valorUnitario, :valorunitariovenda, :valorDesconto, :valoracrescimo, :valorTotal,
                 :quantidade, :codigocliente, :dataRegistro, :situacaoRegistro, :movnota_id)
            """)

            db.execute(sql_insert_item, {
                "empresa": empresa,
                "numerodocumento": numerodocumento,
                "codigovendedor": codigovendedor,
                "codigoproduto": item.get("codigoproduto"),
                "idpedido": idpedido,
                "descricaoproduto": item.get("descricaoproduto"),
                "valorUnitario": valor_unitario,
                "valorunitariovenda": item.get("valorunitariovenda", valor_unitario),
                "valorDesconto": item.get("valorDesconto", 0),
                "valoracrescimo": item.get("valoracrescimo", 0),
                "valorTotal": total_item,
                "quantidade": quantidade,
                "codigocliente": codigocliente,
                "dataRegistro": data_formatada,
                "situacaoRegistro": item.get("situacaoRegistro", "I"),
                "movnota_id": numerodocumento
            })

            db.commit()
            return {
                "success": True,
                "message": "Item adicionado com sucesso!",
                "empresa": empresa,
                "numerodocumento": numerodocumento,
                "codigocliente": codigocliente,
                "codigovendedor": codigovendedor,
                "codigocondPagamento": codigocondPagamento
            }

        except Exception as e:
            db.rollback()
            import traceback
            traceback.print_exc()
            logging.error("❌ Erro ao adicionar item no pedido: %s", str(e))
            raise HTTPException(status_code=500, detail=f"Erro ao salvar item: {str(e)}")


@mov_pedido_router.get("/listar-itens")
async def listar_itens_pedido(token: str = Query(...), empresa: int = Query(...), numerodocumento: int = Query(...)):
    nome_banco = get_nome_banco_por_token(token)
    if not nome_banco:
        raise HTTPException(status_code=403, detail="Token inválido")

    session_empresa = get_empresa_session(nome_banco)
    with session_empresa as db:
        try:
            # 1. Busca primeiro o cliente correspondente na movnota para garantir a consistência
            sql_busca_cliente = text("""
                SELECT codigocliente 
                FROM movnota 
                WHERE empresa = :empresa AND numerodocumento = :numerodocumento AND situacaoRegistro <> 'E'
            """)
            res_cliente = db.execute(sql_busca_cliente,
                                     {"empresa": empresa, "numerodocumento": numerodocumento}).fetchone()

            if not res_cliente:
                raise HTTPException(status_code=404, detail="Pedido não encontrado ou sem cliente vinculado.")

            codigocliente_atual = res_cliente._mapping["codigocliente"]

            # 2. Executa a listagem cruzando rigorosamente com as chaves da movnota
            sql_itens = text("""
                SELECT A.codigoproduto, A.descricaoproduto, A.quantidade, A.valorUnitario, 
                       A.valorDesconto, A.valoracrescimo, A.valorTotal 
                FROM movnotaitem A
                INNER JOIN movnota B ON
                    A.codigocliente = B.codigocliente AND
                    A.numerodocumento = B.numerodocumento AND
                    A.empresa = B.empresa
                WHERE A.empresa = :empresa AND 
                      B.codigocliente = :codigocliente AND
                      A.numerodocumento = :numerodocumento AND
                      A.situacaoRegistro <> 'E'
            """)

            resultados = db.execute(sql_itens, {
                "empresa": empresa,
                "codigocliente": codigocliente_atual,
                "numerodocumento": numerodocumento
            }).mappings().all()

            itens = []
            total_bruto = 0
            total_desconto = 0
            total_acrescimo = 0
            total_liquido = 0

            for r in resultados:
                qtd = float(r["quantidade"] or 0)
                unit = float(r["valorUnitario"] or 0)
                desc = float(r["valorDesconto"] or 0)
                acres = float(r["valoracrescimo"] or 0)
                vlr_total = float(r["valorTotal"] or (qtd * unit))

                total_bruto += (qtd * unit)
                total_desconto += desc
                total_acrescimo += acres
                total_liquido += vlr_total

                itens.append({
                    "codigoproduto": r["codigoproduto"],
                    "descricaoproduto": r["descricaoproduto"],
                    "quantidade": qtd,
                    "valorUnitario": unit,
                    "valorDesconto": desc,
                    "valoracrescimo": acres,
                    "valorTotal": vlr_total
                })

            return {
                "success": True,
                "itens": itens,
                "totais": {
                    "bruto": total_bruto,
                    "desconto": total_desconto,
                    "acrescimo": total_acrescimo,
                    "liquido": total_liquido
                }
            }

        except HTTPException as he:
            raise he
        except Exception as e:
            import traceback
            traceback.print_exc()
            logging.error("❌ Erro ao listar itens do pedido: %s", str(e))
            raise HTTPException(status_code=500, detail=f"Erro ao listar itens: {str(e)}")