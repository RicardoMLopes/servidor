from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
import hashlib
import traceback
from fastapi import Query
from datetime import datetime
from starlette.responses import JSONResponse
from database.connection import get_empresa_session, DB_CHAVE
from function.funtions import gerar_token_cnpj
from model.dictionary import criar_tabela_cadusers_se_nao_existir
from model.pedido import colunas_movnota, colunas_movnotaitem, pks_movnotaitem, pks_movnota
from database.dependencies import get_empresa_db, get_nome_banco_por_token
from database.querys import inserir_pedido  # função separada que faz a inserção
from params.alerta import enviar_alerta
from typing import Optional


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


from fastapi import Request, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")  # coloque sua pasta de templates
templates.env.globals['now'] = datetime.now

@pedido_router.get("/", response_class=HTMLResponse)
async def relatorio_pedido_template(
    request: Request,
    empresa: str = Query(None),  # opcional
    cnpj: str = Query(None),     # opcional
    tipo: str = Query("analitico"),
    numerodocumento: int = Query(None),
    cliente: str = Query(None),
    data_inicio: str = Query(None),
    data_fim: str = Query(None),
    agrupamento: str = Query("pedido")
):
    relatorio = []

    # Só busca dados se filtros principais estiverem preenchidos
    if empresa or cnpj or numerodocumento or cliente or data_inicio or data_fim:
        # Gerar token e abrir conexão com o banco da empresa
        token = gerar_token_cnpj(cnpj, DB_CHAVE)
        nome_banco = get_nome_banco_por_token(token)
        db = get_empresa_session(nome_banco)

        # Montar filtros dinamicamente
        filtros = ["empresa = ?"]
        parametros = [empresa]

        if numerodocumento:
            filtros.append("numerodocumento = ?")
            parametros.append(numerodocumento)
        if cliente:
            filtros.append("(codigocliente = ? OR nomecliente LIKE ?)")
            parametros.append(cliente)
            parametros.append(f"%{cliente}%")
        if data_inicio:
            filtros.append("dataLancamento >= ?")
            parametros.append(data_inicio)
        if data_fim:
            filtros.append("dataLancamento <= ?")
            parametros.append(data_fim)

        where_clause = " AND ".join(filtros)

        # Buscar pedidos
        pedidos = db.execute(f"""
            SELECT numerodocumento, codigovendedor, nomecliente, dataLancamento, codigocondPagamento
            FROM movnota
            WHERE {where_clause}
            ORDER BY dataLancamento, numerodocumento
        """, parametros).fetchall()

        # Função interna para buscar itens e totais de um pedido
        def get_itens_e_totais(numerodoc):
            itens = db.execute("""
                SELECT codigoproduto, descricaoproduto, quantidade,
                       valorunitariovenda, valorDesconto, valoracrescimo, valorTotal
                FROM movnotaitem
                WHERE empresa = ? AND numerodocumento = ?
            """, (empresa, numerodoc)).fetchall()
            totals = db.execute("""
                SELECT SUM(valorDesconto) as totalDesconto,
                       SUM(valoracrescimo) as totalAcrescimo,
                       SUM(valorTotal) as totalGeral
                FROM movnotaitem
                WHERE empresa = ? AND numerodocumento = ?
            """, (empresa, numerodoc)).fetchone()
            return [dict(i) for i in itens], dict(totals)

        # Montar relatório
        if tipo == "analitico":
            for p in pedidos:
                itens, totals = get_itens_e_totais(p["numerodocumento"])
                relatorio.append({
                    "cabecalho": dict(p),
                    "itens": itens,
                    "totalizadores": totals,
                    "forma_pagamento": p["codigocondPagamento"]
                })
        elif tipo == "sintetico":
            for p in pedidos:
                _, totals = get_itens_e_totais(p["numerodocumento"])
                relatorio.append({
                    "cabecalho": dict(p),
                    "totalizadores": totals,
                    "forma_pagamento": p["codigocondPagamento"]
                })
        else:
            raise HTTPException(status_code=400, detail="Tipo de relatório inválido")

        # Aplicar agrupamento se necessário
        if agrupamento != "pedido":
            chave_map = {"cliente": "nomecliente", "vendedor": "codigovendedor"}
            agrupado = {}
            for r in relatorio:
                key = r["cabecalho"].get(chave_map[agrupamento])
                if key not in agrupado:
                    agrupado[key] = {
                        "cabecalho": {"agrupamento": key},
                        "itens": r.get("itens", []),
                        "totalizadores": r["totalizadores"].copy()
                    }
                else:
                    if "itens" in r:
                        agrupado[key]["itens"].extend(r["itens"])
                    for t_key in ["totalDesconto", "totalAcrescimo", "totalGeral"]:
                        agrupado[key]["totalizadores"][t_key] += r["totalizadores"][t_key]
            relatorio = list(agrupado.values())

    # Renderiza template
    return templates.TemplateResponse(
        "pedido/relatorio_pedido.html",
        {
            "request": request,
            "relatorio": relatorio,
            "empresa": empresa,
            "cnpj": cnpj,
            "tipo": tipo,
            "numerodocumento": numerodocumento,
            "cliente": cliente,
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "agrupamento": agrupamento
        }
    )
