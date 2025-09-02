import logging

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
from database.querys import inserir_pedido, ConsultaEmpresa  # função separada que faz a inserção
from params.alerta import enviar_alerta
from typing import Optional
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


pedido_router = APIRouter()
templates = Jinja2Templates(directory="templates")
templates.env.globals['now'] = datetime.now

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



# ==========================================================================================|
#                   RELATÓRIO -  GERAÇÃO DO PEDIDO DE VENDA                                 |
#===========================================================================================|

@pedido_router.get("/", response_class=HTMLResponse)
async def relatorio_pedido_template(
    request: Request,
    empresa: str = Query(None),
    cnpj: str = Query(None),
    token: str = Query(None),
    tipo: str = Query("analitico"),
    numerodocumento: Optional[str] = Query(None),
    cliente: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    agrupamento: Optional[str] = Query(None),
    status: Optional[str] = Query("todos"),
):
    relatorio = []

    # Gera token a partir do CNPJ se necessário
    if not token and cnpj:
        token = gerar_token_cnpj(cnpj, DB_CHAVE)

    if not token:
        return templates.TemplateResponse(
            "pedido/relatorio_pedido.html",
            {
                "request": request,
                "relatorio": [],
                "tipo": tipo,
                "empresa_nome": None,
                "cliente": "",
                "data_inicio": data_inicio,
                "data_fim": data_fim,
                "numerodocumento": "",
                "agrupamento": "",
                "status": status,
                "cnpj": cnpj,
                "token": token
            }
        )

    nome_banco = get_nome_banco_por_token(token)
    if not nome_banco:
        raise HTTPException(status_code=403, detail="Token inválido ou empresa não encontrada")

    db = get_empresa_session(nome_banco)

    empresa_war = ConsultaEmpresa(db)
    codigo_empresa = int(str(empresa_war[0]).lstrip("0"))
    nome_empresa = str(empresa_war[1]) if len(empresa_war) > 1 else "Empresa"

    try:
        numerodocumento = int(numerodocumento) if numerodocumento else None
    except ValueError:
        numerodocumento = None

    filtros = ["A.empresa = :empresa"]
    parametros = {"empresa": codigo_empresa}

    if numerodocumento is not None:
        filtros.append("A.numerodocumento = :numerodocumento")
        parametros["numerodocumento"] = numerodocumento

    if cliente and cliente.strip() and cliente.lower() != "none":
        filtros.append("(A.codigocliente = :cliente OR A.nomecliente LIKE :cliente_like)")
        parametros["cliente"] = cliente
        parametros["cliente_like"] = f"%{cliente}%"

    if data_inicio and data_fim and data_inicio.strip() and data_fim.strip():
        filtros.append("A.dataLancamento BETWEEN :data_inicio AND :data_fim")
        parametros["data_inicio"] = f"{data_inicio} 00:00:00"
        parametros["data_fim"] = f"{data_fim} 23:59:59"

    if agrupamento and agrupamento.strip() and agrupamento.lower() != "none":
        filtros.append("P.agrupamento LIKE :agrupamento")
        parametros["agrupamento"] = f"%{agrupamento}%"

    # Ajuste de status para evitar problemas com espaços e maiúsculas/minúsculas
    status = status.strip().lower() if status else "todos"
    if status != "todos":
        if status == "pendente":
            filtros.append("TRIM(UPPER(A.status)) = 'P'")
        elif status == "enviado":
            filtros.append("TRIM(UPPER(A.status)) = 'R'")

    if len(filtros) <= 1:
        return templates.TemplateResponse(
            "pedido/relatorio_pedido.html",
            {
                "request": request,
                "relatorio": [],
                "tipo": tipo,
                "empresa_nome": nome_empresa,
                "cliente": "",
                "data_inicio": data_inicio,
                "data_fim": data_fim,
                "numerodocumento": "",
                "agrupamento": "",
                "status": status,
                "cnpj": cnpj,
                "token": token
            }
        )

    where_clause = " AND ".join(filtros)

    sql = f"""
        SELECT A.numerodocumento, A.codigovendedor, V.nome as nomevendedor, A.codigocliente, A.nomecliente, A.dataLancamento,
               A.codigocondPagamento, F.descricao as formapagamento, A.status,
               B.codigoproduto, B.descricaoproduto, B.quantidade,
               B.valorunitariovenda, B.valorDesconto, B.valoracrescimo, B.valorTotal,
               P.unidadeMedida
        FROM movnota A
        LEFT JOIN movnotaitem B
            ON A.empresa = B.empresa AND A.numerodocumento = B.numerodocumento AND A.codigocliente = B.codigocliente
        LEFT JOIN cadproduto P
            ON A.empresa = P.empresa AND B.codigoproduto = P.codigo
        LEFT JOIN cadvendedor V
            ON A.empresa = V.empresa AND A.codigovendedor = V.codigo
        LEFT JOIN cadcondicaopagamento F
            ON A.empresa = F.empresa AND A.codigocondPagamento = F.codigo
        WHERE {where_clause}
        ORDER BY A.dataLancamento, A.numerodocumento
    """
    logging.warning("SQL executado: %s", sql)
    logging.warning("Parâmetros: %s", parametros)

    pedidos = db.execute(text(sql), parametros).fetchall()

    status_count = {"P": 0, "R": 0}

    if tipo == "sintetico":
        pedidos_dict_sintetico = {}
        for p in pedidos:
            if p._mapping["status"] in status_count:
                status_count[p._mapping["status"]] += 1

            cliente_key = p._mapping["nomecliente"]
            if cliente_key not in pedidos_dict_sintetico:
                pedidos_dict_sintetico[cliente_key] = {
                    "cabecalho": {
                        "nomecliente": cliente_key,
                        "codigovendedor": p._mapping["codigovendedor"],
                        "nomevendedor": p._mapping["nomevendedor"],
                    },
                    "totalizadores": {"totalDesconto":0,"totalAcrescimo":0,"totalGeral":0,"totalPedidos":0}
                }

            pedidos_dict_sintetico[cliente_key]["totalizadores"]["totalDesconto"] += float(p._mapping["valorDesconto"] or 0)
            pedidos_dict_sintetico[cliente_key]["totalizadores"]["totalAcrescimo"] += float(p._mapping["valoracrescimo"] or 0)
            pedidos_dict_sintetico[cliente_key]["totalizadores"]["totalGeral"] += float(p._mapping["valorTotal"] or 0)
            pedidos_dict_sintetico[cliente_key]["totalizadores"]["totalPedidos"] += 1

        relatorio = list(pedidos_dict_sintetico.values())
    else:
        pedidos_dict = {}
        for p in pedidos:
            numdoc = p._mapping["numerodocumento"]
            status_doc = p._mapping["status"]

            if status_doc in status_count:
                status_count[status_doc] += 1

            if numdoc not in pedidos_dict:
                pedidos_dict[numdoc] = {
                    "cabecalho": dict(p._mapping),
                    "itens": [],
                    "totalizadores": {"totalDesconto":0,"totalAcrescimo":0,"totalGeral":0},
                }

            pedidos_dict[numdoc]["itens"].append({
                "codigoproduto": p._mapping["codigoproduto"],
                "descricaoproduto": p._mapping["descricaoproduto"],
                "quantidade": p._mapping["quantidade"] or 0,
                "valorunitariovenda": float(p._mapping["valorunitariovenda"] or 0),
                "valorDesconto": float(p._mapping["valorDesconto"] or 0),
                "valoracrescimo": float(p._mapping["valoracrescimo"] or 0),
                "valorTotal": float(p._mapping["valorTotal"] or 0),
            })

            pedidos_dict[numdoc]["totalizadores"]["totalDesconto"] += float(p._mapping["valorDesconto"] or 0)
            pedidos_dict[numdoc]["totalizadores"]["totalAcrescimo"] += float(p._mapping["valoracrescimo"] or 0)
            pedidos_dict[numdoc]["totalizadores"]["totalGeral"] += float(p._mapping["valorTotal"] or 0)

        relatorio = list(pedidos_dict.values())

    return templates.TemplateResponse(
        "pedido/relatorio_pedido.html",
        {
            "request": request,
            "relatorio": relatorio,
            "tipo": tipo,
            "empresa_nome": nome_empresa,
            "cliente": "",
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "numerodocumento": "",
            "agrupamento": "",
            "status": status,
            "cnpj": cnpj,
            "token": token,
            "status_count": status_count
        }
    )

