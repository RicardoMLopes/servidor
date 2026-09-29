from __future__ import annotations
import logging
from fastapi import APIRouter, Depends, Form, Request, status
from sqlalchemy.orm import Session
import hashlib
import traceback
from datetime import datetime, date
from database.connection import get_empresa_session, DB_CHAVE
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
async def tela_novo_pedido(
    request: Request,
    numerodocumento: Optional[int] = Query(None),
    tipodocumento: Optional[str] = Query("COTACAO")
):
    print("\n" + "=" * 80)
    print("🚀 [NOVO PEDIDO] INÍCIO DA ROTA /novo")
    print(f"📥 [NOVO PEDIDO] numerodocumento recebido: {numerodocumento}")
    print(f"📥 [NOVO PEDIDO] tipodocumento recebido: {tipodocumento}")
    print(f"🌐 [NOVO PEDIDO] URL completa: {request.url}")
    print("=" * 80)

    empresa_token = request.cookies.get("empresa_token")
    empresa_cnpj = request.cookies.get("empresa_cnpj")
    usuario_id = request.cookies.get("usuario_id")

    print("🍪 [NOVO PEDIDO] Cookies:")
    print(f"   empresa_token: {'SIM' if empresa_token else 'NÃO'}")
    print(f"   empresa_cnpj: {empresa_cnpj}")
    print(f"   usuario_id: {usuario_id}")

    tipodocumento = str(tipodocumento or "COTACAO").strip().upper()

    if tipodocumento not in ("COTACAO", "PEDIDO"):
        print(
            f"⚠️ [NOVO PEDIDO] Tipo inválido recebido. "
            f"Alterando para COTACAO: {tipodocumento}"
        )
        tipodocumento = "COTACAO"

    print(f"📄 [NOVO PEDIDO] Tipo final: {tipodocumento}")

    if not empresa_token or not empresa_cnpj or not usuario_id:
        print("❌ [NOVO PEDIDO] Sessão inválida. Redirecionando login.")
        return RedirectResponse("/login-usuario", status_code=303)

    nome_banco = get_nome_banco_por_token(empresa_token)

    print(f"🏢 [NOVO PEDIDO] Banco encontrado: {nome_banco}")

    if not nome_banco:
        print("❌ [NOVO PEDIDO] Empresa não encontrada pelo token.")
        raise HTTPException(
            status_code=403,
            detail="Empresa não encontrada."
        )

    session_empresa = get_empresa_session(nome_banco)

    codigo_vendedor = ""
    nome_vendedor = ""
    codigo_empresa = 0
    codigo_cliente_padrao = ""
    nome_cliente_padrao = "Nenhum cliente selecionado"
    doc_cliente_padrao = "—"
    codigo_cond_pagamento_padrao = "001"
    nome_cond_pagamento_padrao = ""

    pedido_existente = None
    itens_pedido = []

    totais_pedido = {
        "bruto": 0,
        "desconto": 0,
        "acrescimo": 0,
        "liquido": 0
    }

    with session_empresa as db:

        # 1. Usuário logado
        user_query = db.execute(
            text("""
                SELECT
                    codigovendedor,
                    empresa,
                    usuario
                FROM cadusers
                WHERE id = :usuario_id
                  AND situacaoregistro <> 'E'
                LIMIT 1
            """),
            {"usuario_id": usuario_id}
        ).fetchone()

        if not user_query:
            print(
                f"❌ [NOVO PEDIDO] Usuário não encontrado: "
                f"{usuario_id}"
            )
            return RedirectResponse("/login-usuario", status_code=303)

        user = user_query._mapping

        print("👤 [NOVO PEDIDO] Usuário encontrado:")
        print(f"   usuario: {user.get('usuario')}")
        print(f"   empresa: {user.get('empresa')}")
        print(f"   vendedor: {user.get('codigovendedor')}")

        if user.get("empresa"):
            codigo_empresa = int(user["empresa"])

        if user.get("codigovendedor"):
            codigo_vendedor = str(
                user["codigovendedor"]
            ).strip()

        print(
            f"🏢 [NOVO PEDIDO] Empresa definida pelo usuário: "
            f"{codigo_empresa}"
        )

        print(
            f"👨‍💼 [NOVO PEDIDO] Vendedor inicial: "
            f"{codigo_vendedor or '(vazio)'}"
        )

        # 2. Parâmetros da empresa
        param_query = db.execute(
            text("""
                SELECT
                    vendedorpadrao,
                    clientepadrao,
                    condicaopagamentopadrao,
                    empresa
                FROM cadparametro
                WHERE empresa = :empresa
                LIMIT 1
            """),
            {
                "empresa": codigo_empresa
            }
        ).fetchone()

        if param_query:
            param = param_query._mapping

            print("⚙️ [NOVO PEDIDO] Parâmetros encontrados:")
            print(f"   empresa: {param.get('empresa')}")
            print(f"   vendedor padrão: {param.get('vendedorpadrao')}")
            print(f"   cliente padrão: {param.get('clientepadrao')}")
            print(
                "   condição padrão: "
                f"{param.get('condicaopagamentopadrao')}"
            )

            if (
                not codigo_vendedor
                and param.get("vendedorpadrao")
            ):
                codigo_vendedor = str(
                    param["vendedorpadrao"]
                ).strip()

            if param.get("condicaopagamentopadrao"):
                codigo_cond_pagamento_padrao = str(
                    param["condicaopagamentopadrao"]
                ).strip()

            cod_cliente_param = param.get("clientepadrao")

            if cod_cliente_param:
                cliente_query = db.execute(
                    text("""
                        SELECT
                            codigo,
                            nome,
                            cpfcnpj
                        FROM cadcliente
                        WHERE codigo = :codigo
                          AND situacaoregistro <> 'E'
                        LIMIT 1
                    """),
                    {
                        "codigo": str(
                            cod_cliente_param
                        ).strip()
                    }
                ).fetchone()

                if cliente_query:
                    cliente = cliente_query._mapping

                    codigo_cliente_padrao = str(
                        cliente.get("codigo", "")
                    ).strip()

                    nome_cliente_padrao = str(
                        cliente.get(
                            "nome",
                            "Cliente Sem Nome"
                        )
                    ).strip()

                    doc_cliente_padrao = str(
                        cliente.get(
                            "cpfcnpj",
                            "—"
                        )
                    ).strip()

                    print("👤 [NOVO PEDIDO] Cliente padrão encontrado:")
                    print(
                        f"   código: {codigo_cliente_padrao}"
                    )
                    print(
                        f"   nome: {nome_cliente_padrao}"
                    )
                else:
                    print(
                        "⚠️ [NOVO PEDIDO] Cliente padrão "
                        f"não encontrado: {cod_cliente_param}"
                    )
        else:
            print(
                "⚠️ [NOVO PEDIDO] Nenhum registro encontrado "
                f"em cadparametro para empresa {codigo_empresa}"
            )

        # 3. Novo documento
        if not numerodocumento:
            print(
                "🆕 [NOVO PEDIDO] Nenhum número recebido. "
                "Calculando próximo número..."
            )

            numero_query = db.execute(
                text("""
                    SELECT COALESCE(
                        MAX(numerodocumento),
                        0
                    ) + 1 AS proximo_numero
                    FROM movnota
                    WHERE empresa = :empresa
                """),
                {
                    "empresa": codigo_empresa
                }
            ).fetchone()

            if numero_query:
                numerodocumento = int(
                    numero_query._mapping[
                        "proximo_numero"
                    ] or 1
                )
            else:
                numerodocumento = 1

            print(
                f"🔢 [NOVO PEDIDO] Próximo número calculado: "
                f"{numerodocumento}"
            )
        else:
            print(
                f"📌 [NOVO PEDIDO] Número recebido pela URL: "
                f"{numerodocumento}"
            )

        # 4. Verifica se esse número já existe
        print(
            "🔎 [NOVO PEDIDO] Verificando existência do documento:"
        )
        print(f"   empresa: {codigo_empresa}")
        print(f"   número: {numerodocumento}")
        print(f"   tipo solicitado: {tipodocumento}")

        nota_query = db.execute(
            text("""
                SELECT
                    n.id,
                    n.empresa,
                    n.numerodocumento,
                    n.codigocliente,
                    c.nome AS nomecliente,
                    c.cpfcnpj AS doccliente,
                    n.codigovendedor,
                    n.codigocondPagamento,
                    n.valorTotal
                FROM movnota n
                LEFT JOIN cadcliente c
                    ON c.codigo = n.codigocliente
                   AND c.situacaoregistro <> 'E'
                WHERE n.empresa = :empresa
                  AND n.numerodocumento = :numerodocumento
                  AND n.situacaoregistro <> 'E'
                LIMIT 1
            """),
            {
                "empresa": codigo_empresa,
                "numerodocumento": numerodocumento
            }
        ).fetchone()

        if nota_query:
            m = nota_query._mapping

            print("🚨 [NOVO PEDIDO] DOCUMENTO JÁ EXISTE!")
            print(f"   id: {m['id']}")
            print(f"   número: {m['numerodocumento']}")
            print(f"   cliente: {m['codigocliente']}")
            print(f"   vendedor: {m['codigovendedor']}")

            pedido_existente = m["numerodocumento"]

            codigo_cliente_padrao = str(
                m["codigocliente"] or ""
            ).strip()

            nome_cliente_padrao = str(
                m["nomecliente"] or "Cliente Sem Nome"
            ).strip()

            doc_cliente_padrao = str(
                m["doccliente"] or "—"
            ).strip()

            codigo_vendedor = str(
                m["codigovendedor"] or codigo_vendedor
            ).strip()

            codigo_cond_pagamento_padrao = str(
                m["codigocondPagamento"]
                or codigo_cond_pagamento_padrao
            ).strip()

            itens_query = db.execute(
                text("""
                    SELECT
                        tipodocumento,
                        codigoproduto,
                        descricaoproduto,
                        quantidade,
                        quantidade_pedida,
                        valorUnitario,
                        valorunitariovenda,
                        valorDesconto,
                        valoracrescimo,
                        valorTotal
                    FROM movnotaitem
                    WHERE empresa = :empresa
                      AND numerodocumento = :numerodocumento
                      AND situacaoregistro <> 'E'
                      AND tipodocumento = :tipodocumento
                    ORDER BY seq
                """),
                {
                    "empresa": codigo_empresa,
                    "numerodocumento": numerodocumento,
                    "tipodocumento": tipodocumento
                }
            ).fetchall()

            print(
                f"📦 [NOVO PEDIDO] Itens encontrados: "
                f"{len(itens_query)}"
            )

            t_bruto = 0
            t_desconto = 0
            t_acrescimo = 0
            t_liquido = 0

            for item in itens_query:
                im = item._mapping

                qtd_original = float(
                    im["quantidade"] or 0
                )

                qtd_pedida = float(
                    im["quantidade_pedida"] or 0
                )

                v_unit = float(
                    im["valorUnitario"] or 0
                )

                v_unit_venda = float(
                    im["valorunitariovenda"] or 0
                )

                v_desc_original = float(
                    im["valorDesconto"] or 0
                )

                v_acres_original = float(
                    im["valoracrescimo"] or 0
                )

                if tipodocumento == "PEDIDO":
                    qtd = qtd_pedida

                    if qtd_original > 0:
                        fator = qtd_pedida / qtd_original
                    else:
                        fator = 0

                    v_desc = round(
                        v_desc_original * fator,
                        2
                    )

                    v_acres = round(
                        v_acres_original * fator,
                        2
                    )
                else:
                    qtd = qtd_original
                    v_desc = v_desc_original
                    v_acres = v_acres_original

                subtotal = round(
                    v_unit_venda * qtd,
                    2
                )

                v_tot = round(
                    subtotal - v_desc + v_acres,
                    2
                )

                t_bruto += subtotal
                t_desconto += v_desc
                t_acrescimo += v_acres
                t_liquido += v_tot

                itens_pedido.append({
                    "codigoproduto": im["codigoproduto"],
                    "descricaoproduto": im["descricaoproduto"],
                    "quantidade": qtd,
                    "quantidade_original": qtd_original,
                    "quantidade_pedida": qtd_pedida,
                    "tipodocumento": tipodocumento,
                    "valorUnitario": v_unit,
                    "valorunitariovenda": v_unit_venda,
                    "valorDesconto": v_desc,
                    "valoracrescimo": v_acres,
                    "valorTotal": v_tot
                })

            totais_pedido = {
                "bruto": t_bruto,
                "desconto": t_desconto,
                "acrescimo": t_acrescimo,
                "liquido": t_liquido
            }

        else:
            print(
                "✅ [NOVO PEDIDO] DOCUMENTO NÃO EXISTE. "
                "Será tratado como NOVO."
            )
            print(
                f"   novo número disponível: {numerodocumento}"
            )

        # 5. Busca nome do vendedor
        if codigo_vendedor:
            vend_cad = db.execute(
                text("""
                    SELECT nome
                    FROM cadvendedor
                    WHERE TRIM(codigo) = :codigo
                      AND empresa = :empresa
                      AND situacaoregistro <> 'E'
                    LIMIT 1
                """),
                {
                    "codigo": codigo_vendedor,
                    "empresa": codigo_empresa
                }
            ).fetchone()

            if vend_cad and vend_cad._mapping.get("nome"):
                nome_vendedor = vend_cad._mapping["nome"]

        # 6. Busca descrição da condição de pagamento
        if codigo_cond_pagamento_padrao:
            cond_cad = db.execute(
                text("""
                    SELECT descricao
                    FROM cadcondicaopagamento
                    WHERE TRIM(codigo) = :codigo
                      AND situacaoregistro <> 'E'
                    LIMIT 1
                """),
                {
                    "codigo": codigo_cond_pagamento_padrao
                }
            ).fetchone()

            if cond_cad and cond_cad._mapping.get("descricao"):
                nome_cond_pagamento_padrao = (
                    cond_cad._mapping["descricao"]
                )

    print("\n📤 [NOVO PEDIDO] DADOS ENVIADOS AO TEMPLATE:")
    print(f"   numerodocumento: {numerodocumento}")
    print(f"   pedido_existente: {pedido_existente}")
    print(f"   tipodocumento: {tipodocumento}")
    print(f"   empresa: {codigo_empresa}")
    print(f"   vendedor: {codigo_vendedor}")
    print(f"   cliente: {codigo_cliente_padrao}")
    print(
        f"   condição pagamento: "
        f"{codigo_cond_pagamento_padrao}"
    )
    print(f"   quantidade de itens: {len(itens_pedido)}")
    print("=" * 80 + "\n")

    return templates.TemplateResponse(
        "pedido/movimento/lancamento_pedido.html",
        {
            "request": request,
            "token": empresa_token,
            "codigo_vendedor": codigo_vendedor,
            "nome_vendedor": nome_vendedor,
            "empresa": codigo_empresa,
            "codigo_cliente_padrao": codigo_cliente_padrao,
            "nome_cliente_padrao": nome_cliente_padrao,
            "doc_cliente_padrao": doc_cliente_padrao,
            "codigo_cond_pagamento_padrao": (
                codigo_cond_pagamento_padrao
            ),
            "nome_cond_pagamento_padrao": (
                nome_cond_pagamento_padrao
            ),
            "pedido_existente": pedido_existente,
            "numerodocumento": numerodocumento,
            "itens_pedido": itens_pedido,
            "totais_pedido": totais_pedido,
            "tipodocumento": tipodocumento
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
async def buscar_produtos(
    token: str = Query(...),
    termo: Optional[str] = Query(None),
    codigocondPagamento: Optional[str] = Query(None)
):
    nome_banco = get_nome_banco_por_token(token)
    if not nome_banco:
        raise HTTPException(status_code=403, detail="Token inválido")

    session_empresa = get_empresa_session(nome_banco)
    with session_empresa as db:
        sql = """
            SELECT codigo, codigobarra, descricao, precoVenda 
            FROM cadproduto 
            WHERE situacaoRegistro <> 'E'
        """
        params = {}

        if termo and termo.strip():
            termo_limpo = termo.strip()

            # 🔹 Se for numérico, trata zeros à esquerda e busca por código exato, com zeros ou código de barras
            if termo_limpo.isdigit():
                termo_zeros = termo_limpo.zfill(5)
                sql += " AND (codigo = :termo OR codigo = :termo_zeros OR codigobarra = :termo)"
                params["termo"] = termo_limpo
                params["termo_zeros"] = termo_zeros
            else:
                sql += " AND descricao LIKE :termo_like"
                params["termo_like"] = f"%{termo_limpo}%"

        sql += " LIMIT 50"

        resultados = db.execute(text(sql), params).fetchall()

        cond_pagto_normalizada = codigocondPagamento.strip() if codigocondPagamento and codigocondPagamento.strip() else None

        produtos = []
        for p in resultados:
            dados = dict(p._mapping) if hasattr(p, "_mapping") else dict(p)
            preco_venda_original = float(dados.get("precoVenda") or 0)

            # Recalcula com base na condição de pagamento
            valor_unitario_calculado, perc_desc, perc_acres = calcular_preco_unitario_condicao(
                db=db,
                codigocondPagamento=cond_pagto_normalizada,
                preco_venda_original=preco_venda_original
            )

            produtos.append({
                "codigo": str(dados.get("codigo")).zfill(5),
                "codigobarra": dados.get("codigobarra"),
                "descricao": dados.get("descricao"),
                "precoVenda": preco_venda_original,
                "valorUnitario": valor_unitario_calculado,
                "percentualDescontoCond": perc_desc,
                "percentualAcrescimoCond": perc_acres
            })

        return {"produtos": produtos}

def calcular_preco_unitario_condicao(db, codigocondPagamento: str, preco_venda_original: float) -> tuple[
    float, float, float]:
    """
    Retorna uma tupla: (valor_unitario_final, perc_desconto, perc_acrescimo)
    """
    if not codigocondPagamento or not str(codigocondPagamento).strip():
        return float(preco_venda_original), 0.0, 0.0

    cod_clean = str(codigocondPagamento).strip()

    # 🔹 Busca a condição com fallback para string/numérico
    cond_query = db.execute(
        text("""
             SELECT acrescimo, desconto
             FROM cadcondicaopagamento
             WHERE TRIM(codigo) = :codigo
               AND situacaoregistro <> 'E' LIMIT 1
             """),
        {"codigo": cod_clean}
    ).fetchone()

    if not cond_query and cod_clean.isdigit():
        cond_query = db.execute(
            text("""
                 SELECT acrescimo, desconto
                 FROM cadcondicaopagamento
                 WHERE CAST(codigo AS UNSIGNED) = :cod_num
                   AND situacaoregistro <> 'E' LIMIT 1
                 """),
            {"cod_num": int(cod_clean)}
        ).fetchone()

    if not cond_query:
        return float(preco_venda_original), 0.0, 0.0

    m = cond_query._mapping
    perc_acrescimo = float(m.get("acrescimo") or 0)
    perc_desconto = float(m.get("desconto") or 0)

    valor_calculado = float(preco_venda_original)

    # 🔹 Aplica Acréscimo (%) se houver
    if perc_acrescimo > 0:
        valor_calculado += (valor_calculado * (perc_acrescimo / 100))

    # 🔹 Aplica Desconto (%) se houver
    if perc_desconto > 0:
        valor_calculado -= (valor_calculado * (perc_desconto / 100))

    return round(valor_calculado, 4), perc_desconto, perc_acrescimo


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

            # 🔹 BLOCO DE VALIDAÇÃO
            if not codigocliente or str(codigocliente).strip() == "":
                raise HTTPException(
                    status_code=400,
                    detail="Nenhum cliente selecionado! Por favor, informe um cliente antes de adicionar o item."
                )

            item = dados.get("item", {})

            tipodocumento = str(dados.get("tipodocumento") or "COTACAO").strip().upper()

            if tipodocumento not in ("COTACAO", "PEDIDO"):
                tipodocumento = "COTACAO"

            quantidade = float(item.get("quantidade", 0))

            quantidade_pedida = (quantidade if tipodocumento == "PEDIDO"  else 0)

            valor_unitario = float(item.get("valorUnitario", 0))

            # 🔹 PREÇO BASE ORIGINAL
            valor_unitario_venda = float(item.get("valorunitariovenda") or valor_unitario)

            valor_desconto = float(item.get("valorDesconto", 0))
            valor_acrescimo = float(item.get("valoracrescimo", 0))
            valor_bruto_item = (quantidade * valor_unitario)

            try:
                data_atual = datetime.now( ZoneInfo("America/Sao_Paulo"))
            except Exception:
                data_atual = datetime.now()
            data_formatada = data_atual.strftime("%Y-%m-%d %H:%M:%S")

            # ============================================================
            # 1. VERIFICA SE O MOVIMENTO (MOVNOTA) JÁ EXISTE
            # ============================================================

            resultado_nota = None

            if numerodocumento:
                sql_busca_nota = text("""
                    SELECT
                        id,
                        valorTotal,
                        codigovendedor,
                        codigocondPagamento,
                        codigocliente
                    FROM movnota
                    WHERE empresa = :empresa
                      AND numerodocumento = :numerodocumento
                    LIMIT 1
                """)

                resultado_nota = db.execute(
                    sql_busca_nota,
                    {
                        "empresa": empresa,
                        "numerodocumento": numerodocumento
                    }
                ).mappings().fetchone()

            # ============================================================
            # 2. REGRAS DE DEFESA/PREENCHIMENTO DE CÓDIGOS
            # ============================================================

            if resultado_nota:
                if (
                    not codigovendedor or
                    str(codigovendedor).strip() == ""
                ):
                    codigovendedor = (
                        resultado_nota["codigovendedor"]
                    )

                if (
                    not codigocondPagamento or
                    str(codigocondPagamento).strip() == ""
                ):
                    codigocondPagamento = (
                        resultado_nota["codigocondPagamento"]
                    )

            else:
                if (
                    not codigocondPagamento or
                    str(codigocondPagamento).strip() == ""
                ):
                    param_query = db.execute(
                        text("""
                            SELECT condicaopagamentopadrao
                            FROM cadparametro
                            LIMIT 1
                        """)
                    ).fetchone()

                    if (
                        param_query and
                        param_query._mapping.get(
                            "condicaopagamentopadrao"
                        )
                    ):
                        codigocondPagamento = str(
                            param_query._mapping[
                                "condicaopagamentopadrao"
                            ]
                        ).strip()

            # ============================================================
            # 3. BUSCA OS NOMES NO CADASTRO
            # ============================================================

            # 3.1 Nome do Cliente
            nome_cliente = dados.get(
                "nomecliente",
                ""
            )

            if codigocliente:
                cli_query = db.execute(
                    text("""
                        SELECT nome
                        FROM cadcliente
                        WHERE codigo = :codigo
                          AND situacaoregistro <> 'E'
                        LIMIT 1
                    """),
                    {
                        "codigo": str(
                            codigocliente
                        ).strip()
                    }
                ).fetchone()

                if (
                    cli_query and
                    cli_query._mapping.get("nome")
                ):
                    nome_cliente = (
                        cli_query._mapping["nome"]
                    )

            # 3.2 Nome do Vendedor
            nome_vendedor = dados.get(
                "nomevendedor",
                ""
            )

            if (
                codigovendedor and
                str(codigovendedor).strip() != ""
            ):
                cod_v_clean = str(
                    codigovendedor
                ).strip()

                vend_query = db.execute(
                    text("""
                        SELECT nome
                        FROM cadvendedor
                        WHERE TRIM(codigo) = :codigo
                          AND empresa = :empresa
                          AND situacaoregistro <> 'E'
                        LIMIT 1
                    """),
                    {
                        "codigo": cod_v_clean,
                        "empresa": empresa
                    }
                ).fetchone()

                if (
                    vend_query and
                    vend_query._mapping.get("nome")
                ):
                    nome_vendedor = (
                        vend_query._mapping["nome"]
                    )

            # 3.3 Nome da Condição de Pagamento
            nome_cond_pagamento = dados.get(
                "nomecondPagamento",
                ""
            )

            if (
                codigocondPagamento and
                str(codigocondPagamento).strip() != ""
            ):
                cod_c_clean = str(
                    codigocondPagamento
                ).strip()

                cond_query = db.execute(
                    text("""
                        SELECT descricao
                        FROM cadcondicaopagamento
                        WHERE TRIM(codigo) = :codigo
                          AND situacaoregistro <> 'E'
                        LIMIT 1
                    """),
                    {
                        "codigo": cod_c_clean
                    }
                ).fetchone()

                if (
                    cond_query and
                    cond_query._mapping.get("descricao")
                ):
                    nome_cond_pagamento = (
                        cond_query._mapping["descricao"]
                    )

            # ============================================================
            # 4. SE NÃO VEIO NUMERODOCUMENTO, GERA O PRÓXIMO
            # ============================================================

            if not numerodocumento:
                result_prox = db.execute(
                    text("""
                        SELECT
                            COALESCE(
                                MAX(numerodocumento),
                                0
                            ) + 1 AS prox
                        FROM movnota
                        WHERE empresa = :empresa
                    """),
                    {
                        "empresa": empresa
                    }
                ).mappings().fetchone()

                numerodocumento = (
                    result_prox["prox"]
                    if result_prox
                    else 1
                )

            if not idpedido:
                idpedido = numerodocumento

            # ============================================================
            # 5. VALIDAÇÃO DE LIMITE DE DESCONTO
            # ============================================================

            vendedor_query = db.execute(
                text("""
                    SELECT limitedesconto
                    FROM cadvendedor
                    WHERE codigo = :vendedor
                      AND empresa = :empresa
                      AND situacaoregistro <> 'E'
                    LIMIT 1
                """),
                {
                    "vendedor": codigovendedor,
                    "empresa": empresa
                }
            ).fetchone()

            limite_vendedor = (
                float(
                    vendedor_query._mapping[
                        "limitedesconto"
                    ] or 0
                )
                if (
                    vendedor_query and
                    vendedor_query._mapping.get(
                        "limitedesconto"
                    ) is not None
                )
                else None
            )

            produto_query = db.execute(
                text("""
                    SELECT percentualDesconto
                    FROM cadproduto
                    WHERE codigo = :produto
                      AND empresa = :empresa
                      AND situacaoregistro <> 'E'
                    LIMIT 1
                """),
                {
                    "produto": item.get(
                        "codigoproduto"
                    ),
                    "empresa": empresa
                }
            ).fetchone()

            limite_produto = (
                float(
                    produto_query._mapping[
                        "percentualDesconto"
                    ] or 0
                )
                if (
                    produto_query and
                    produto_query._mapping.get(
                        "percentualDesconto"
                    ) is not None
                )
                else None
            )

            limite_maximo_permitido = (
                limite_vendedor
                if limite_vendedor is not None
                else limite_produto
            )

            if (
                valor_bruto_item > 0 and
                limite_maximo_permitido is not None
            ):
                percentual_aplicado = (
                    valor_desconto /
                    valor_bruto_item
                ) * 100

                if (
                    percentual_aplicado >
                    limite_maximo_permitido
                ):
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"Desconto de "
                            f"{percentual_aplicado:.2f}% "
                            f"excede o limite máximo permitido "
                            f"de "
                            f"{limite_maximo_permitido:.2f}%."
                        )
                    )

            # ============================================================
            # 6. CÁLCULO DO TOTAL LÍQUIDO DO ITEM
            # ============================================================

            total_item = (
                valor_bruto_item -
                valor_desconto +
                valor_acrescimo
            )

            if total_item < 0:
                total_item = 0.0

            # ============================================================
            # 7. INSERE OU ATUALIZA O CABEÇALHO (MOVNOTA)
            # ============================================================

            if not resultado_nota:
                sql_insert_nota = text("""
                    INSERT INTO movnota
                    (
                        empresa,
                        numerodocumento,
                        codigocondPagamento,
                        codigovendedor,
                        codigocliente,
                        nomecliente,
                        idpedido,
                        valorDesconto,
                        valorDespesas,
                        valorFrete,
                        valorTotal,
                        pesoTotal,
                        observacao,
                        status,
                        dataLancamento,
                        situacaoRegistro,
                        dataRegistro,
                        pedido_hash
                    )
                    VALUES
                    (
                        :empresa,
                        :numerodocumento,
                        :codigocondPagamento,
                        :codigovendedor,
                        :codigocliente,
                        :nomecliente,
                        :idpedido,
                        :valorDesconto,
                        :valorDespesas,
                        :valorFrete,
                        :valorTotal,
                        :pesoTotal,
                        :observacao,
                        :status,
                        :dataLancamento,
                        :situacaoRegistro,
                        :dataRegistro,
                        :pedido_hash
                    )
                """)

                db.execute(
                    sql_insert_nota,
                    {
                        "empresa": empresa,
                        "numerodocumento": numerodocumento,
                        "codigocondPagamento": codigocondPagamento,
                        "codigovendedor": codigovendedor,
                        "codigocliente": codigocliente,
                        "nomecliente": nome_cliente,
                        "idpedido": idpedido,
                        "valorDesconto": dados.get(
                            "valorDesconto",
                            0
                        ),
                        "valorDespesas": dados.get(
                            "valorDespesas",
                            0
                        ),
                        "valorFrete": dados.get(
                            "valorFrete",
                            0
                        ),
                        "valorTotal": total_item,
                        "pesoTotal": dados.get(
                            "pesoTotal",
                            0
                        ),
                        "observacao": dados.get(
                            "observacao",
                            ""
                        ),
                        "status": dados.get(
                            "status",
                            "P"
                        ),
                        "dataLancamento": data_formatada,
                        "situacaoRegistro": dados.get(
                            "situacaoRegistro",
                            "I"
                        ),
                        "dataRegistro": data_formatada,
                        "pedido_hash": dados.get(
                            "pedido_hash"
                        )
                    }
                )

                # 🔹 Busca o ID real gerado no MOVNOTA
                resultado_movnota = db.execute(
                    text("""
                        SELECT id
                        FROM movnota
                        WHERE empresa = :empresa
                          AND numerodocumento = :numerodocumento
                        LIMIT 1
                    """),
                    {
                        "empresa": empresa,
                        "numerodocumento": numerodocumento
                    }
                ).mappings().fetchone()

            else:
                novo_valor_total = (
                    float(
                        resultado_nota["valorTotal"]
                    ) +
                    total_item
                )

                sql_update_nota = text("""
                    UPDATE movnota
                    SET valorTotal = :novo_valor_total,
                        codigocliente = :codigocliente,
                        nomecliente = :nomecliente,
                        codigovendedor = :codigovendedor,
                        codigocondPagamento = :codigocondPagamento
                    WHERE empresa = :empresa
                      AND numerodocumento = :numerodocumento
                """)

                db.execute(
                    sql_update_nota,
                    {
                        "novo_valor_total": novo_valor_total,
                        "codigocliente": codigocliente,
                        "nomecliente": nome_cliente,
                        "codigovendedor": codigovendedor,
                        "codigocondPagamento": codigocondPagamento,
                        "empresa": empresa,
                        "numerodocumento": numerodocumento
                    }
                )

                # 🔹 O ID já veio da consulta inicial
                resultado_movnota = {
                    "id": resultado_nota["id"]
                }

            # ============================================================
            # 🔹 ID REAL DO MOVNOTA
            # ============================================================

            if not resultado_movnota:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        "Não foi possível localizar o ID "
                        "do movimento (movnota)."
                    )
                )

            movnota_id = resultado_movnota["id"]

            logging.info(
                "🔗 MOVNOTA localizado: id=%s, empresa=%s, numerodocumento=%s",
                movnota_id,
                empresa,
                numerodocumento
            )

            # ============================================================
            # 8. DESCOBRE O PRÓXIMO SEQ E INSERE O ITEM
            # ============================================================

            result_seq = db.execute(
                text("""
                    SELECT
                        COALESCE(MAX(seq), 0) + 1 AS proq_seq
                    FROM movnotaitem
                    WHERE empresa = :empresa
                      AND numerodocumento = :numerodocumento
                """),
                {
                    "empresa": empresa,
                    "numerodocumento": numerodocumento
                }
            ).mappings().fetchone()

            proxima_seq = (
                result_seq["proq_seq"]
                if result_seq
                else 1
            )

            sql_insert_item = text("""
                INSERT INTO movnotaitem
                (
                    empresa,
                    numerodocumento,
                    seq,
                    codigovendedor,
                    codigoproduto,
                    idpedido,
                    descricaoproduto,
                    valorUnitario,
                    valorunitariovenda,
                    valorDesconto,
                    valoracrescimo,
                    valorTotal,
                    quantidade,
                    quantidade_pedida,
                    tipodocumento,
                    codigocliente,
                    dataRegistro,
                    situacaoRegistro,
                    movnota_id
                )
                VALUES
                (
                    :empresa,
                    :numerodocumento,
                    :seq,
                    :codigovendedor,
                    :codigoproduto,
                    :idpedido,
                    :descricaoproduto,
                    :valorUnitario,
                    :valorunitariovenda,
                    :valorDesconto,
                    :valoracrescimo,
                    :valorTotal,
                    :quantidade,
                    :quantidade_pedida,
                    :tipodocumento,
                    :codigocliente,
                    :dataRegistro,
                    :situacaoRegistro,
                    :movnota_id
                )
            """)

            db.execute(
                sql_insert_item,
                {
                    "empresa": empresa,
                    "numerodocumento": numerodocumento,
                    "seq": proxima_seq,
                    "codigovendedor": codigovendedor,
                    "codigoproduto": item.get(
                        "codigoproduto"
                    ),
                    "idpedido": idpedido,
                    "descricaoproduto": item.get(
                        "descricaoproduto"
                    ),
                    "valorUnitario": valor_unitario,
                    "valorunitariovenda": valor_unitario_venda,
                    "valorDesconto": valor_desconto,
                    "valoracrescimo": valor_acrescimo,
                    "valorTotal": total_item,
                    "quantidade": quantidade,
                    "quantidade_pedida": quantidade_pedida,
                    "tipodocumento": tipodocumento,
                    "codigocliente": codigocliente,
                    "dataRegistro": data_formatada,
                    "situacaoRegistro": item.get(
                        "situacaoRegistro",
                        "I"
                    ),
                    "movnota_id": movnota_id
                }
            )

            db.commit()

            # ============================================================
            # 9. RETORNO COMPLETO
            # ============================================================

            return {
                "success": True,
                "message": "Item adicionado com sucesso!",
                "empresa": empresa,
                "numerodocumento": numerodocumento,
                "codigocliente": codigocliente,
                "nomecliente": nome_cliente,
                "codigovendedor": codigovendedor,
                "nomevendedor": nome_vendedor,
                "codigocondPagamento": codigocondPagamento,
                "nomecondPagamento": nome_cond_pagamento
            }

        except HTTPException:
            db.rollback()
            raise

        except Exception as e:
            db.rollback()

            import traceback
            traceback.print_exc()

            logging.error(
                "❌ Erro ao adicionar item no pedido: %s",
                str(e)
            )

            raise HTTPException(
                status_code=500,
                detail=f"Erro ao salvar item: {str(e)}"
            )

@mov_pedido_router.get("/listar-itens")
async def listar_itens_pedido(token: str = Query(...), empresa: int = Query(...), numerodocumento: int = Query(...)):
    nome_banco = get_nome_banco_por_token(token)
    if not nome_banco:
        raise HTTPException(status_code=403, detail="Token inválido")

    session_empresa = get_empresa_session(nome_banco)
    with session_empresa as db:
        try:
            # 1. Busca o movimento
            sql_busca_nota = text("""
                SELECT codigocliente, codigovendedor, codigocondPagamento 
                FROM movnota 
                WHERE empresa = :empresa 
                  AND numerodocumento = :numerodocumento 
                  AND situacaoRegistro <> 'E'
                LIMIT 1
            """)
            res_nota = db.execute(sql_busca_nota, {
                "empresa": empresa,
                "numerodocumento": numerodocumento
            }).fetchone()

            if not res_nota:
                raise HTTPException(status_code=404, detail="Pedido não encontrado.")

            codigocliente_atual = str(res_nota._mapping["codigocliente"] or "").strip()
            codigovendedor_atual = str(res_nota._mapping["codigovendedor"] or "").strip()
            codigocond_atual = str(res_nota._mapping["codigocondPagamento"] or "").strip()

            # 🔹 2. Busca CLIENTE no Cadastro
            nomecliente = ""
            doccliente = ""
            if codigocliente_atual:
                cli_cad = db.execute(
                    text("SELECT nome, cpfcnpj FROM cadcliente WHERE codigo = :codigo AND situacaoregistro <> 'E' LIMIT 1"),
                    {"codigo": codigocliente_atual}
                ).fetchone()
                if cli_cad:
                    nomecliente = cli_cad._mapping.get("nome", "") or ""
                    doccliente = cli_cad._mapping.get("cpfcnpj", "") or ""

            # 🔹 3. Busca VENDEDOR no Cadastro (Trata "00518" vs "518")
            nomevendedor = ""
            if codigovendedor_atual:
                vend_query = db.execute(
                    text("""
                        SELECT nome FROM cadvendedor 
                        WHERE TRIM(codigo) = :codigo AND empresa = :empresa AND situacaoregistro <> 'E' 
                        LIMIT 1
                    """),
                    {"codigo": codigovendedor_atual, "empresa": empresa}
                ).fetchone()

                # Fallback: Se não achar como string, tenta convertendo para número puro (ex: 518)
                if not vend_query and codigovendedor_atual.isdigit():
                    vend_query = db.execute(
                        text("""
                            SELECT nome FROM cadvendedor 
                            WHERE CAST(codigo AS UNSIGNED) = :cod_num AND empresa = :empresa AND situacaoregistro <> 'E' 
                            LIMIT 1
                        """),
                        {"cod_num": int(codigovendedor_atual), "empresa": empresa}
                    ).fetchone()

                if vend_query:
                    nomevendedor = vend_query._mapping.get("nome", "") or ""

            # 🔹 4. Busca CONDIÇÃO DE PAGAMENTO no Cadastro (Trata "001" vs "1")
            nomecondPagamento = ""
            if codigocond_atual:
                cond_query = db.execute(
                    text("""
                        SELECT descricao FROM cadcondicaopagamento 
                        WHERE TRIM(codigo) = :codigo AND situacaoregistro <> 'E' 
                        LIMIT 1
                    """),
                    {"codigo": codigocond_atual}
                ).fetchone()

                # Fallback: Se não achar como string, tenta convertendo para número puro (ex: 1)
                if not cond_query and codigocond_atual.isdigit():
                    cond_query = db.execute(
                        text("""
                            SELECT descricao FROM cadcondicaopagamento 
                            WHERE CAST(codigo AS UNSIGNED) = :cod_num AND situacaoregistro <> 'E' 
                            LIMIT 1
                        """),
                        {"cod_num": int(codigocond_atual)}
                    ).fetchone()

                if cond_query:
                    nomecondPagamento = cond_query._mapping.get("descricao", "") or ""

            # 🔹 5. Busca Itens do Pedido
            sql_itens = text("""
                SELECT A.seq, A.codigoproduto, A.descricaoproduto, A.quantidade, A.valorUnitario, 
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
                    "seq": r["seq"],
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
                "codigocliente": codigocliente_atual,
                "nomecliente": nomecliente,
                "doccliente": doccliente,
                "codigovendedor": codigovendedor_atual,
                "nomevendedor": nomevendedor,
                "codigocondPagamento": codigocond_atual,
                "nomecondPagamento": nomecondPagamento,
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


@mov_pedido_router.get("/limite-desconto")
async def obter_limite_desconto(
    token: str = Query(...),
    codigovendedor: str = Query(...),
    codigoproduto: str = Query(...)
):
    nome_banco = get_nome_banco_por_token(token)
    if not nome_banco:
        raise HTTPException(status_code=403, detail="Token inválido")

    session_empresa = get_empresa_session(nome_banco)
    with session_empresa as db:
        try:
            # 1. Busca o limite do vendedor
            vendedor_query = db.execute(
                text("SELECT limitedesconto FROM cadvendedor WHERE codigo = :vendedor AND situacaoregistro <> 'E' LIMIT 1"),
                {"vendedor": codigovendedor}
            ).fetchone()
            limite_vendedor = float(vendedor_query._mapping["limitedesconto"]) if vendedor_query and vendedor_query._mapping.get("limitedesconto") is not None else None

            # 2. Busca o limite do produto
            produto_query = db.execute(
                text("SELECT percentualDesconto FROM cadproduto WHERE codigo = :produto AND situacaoregistro <> 'E' LIMIT 1"),
                {"produto": codigoproduto}
            ).fetchone()
            limite_produto = float(produto_query._mapping["percentualDesconto"]) if produto_query and produto_query._mapping.get("percentualDesconto") is not None else None

            # 3. Regra: Prevalece o do vendedor se houver, senão o do produto
            limite_maximo = limite_vendedor if limite_vendedor is not None else limite_produto

            return {
                "success": True,
                "limiteMaximoPercentual": limite_maximo if limite_maximo is not None else 100.0
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao buscar limite: {str(e)}")


@mov_pedido_router.get("/listar-opcoes-condicoes")
async def listar_opcoes_condicoes(token: Optional[str] = Query(None)):
    if not token:
        raise HTTPException(status_code=400, detail="Token não fornecido.")

    nome_banco = get_nome_banco_por_token(token)
    if not nome_banco:
        raise HTTPException(status_code=403, detail="Empresa não encontrada.")

    session_empresa = get_empresa_session(nome_banco)

    try:
        with session_empresa as db:
            # Busca vendedores ativos (Verifique se os nomes das colunas batem com sua tabela cadvendedor)
            vendedores_query = db.execute(
                text("SELECT codigo, nome FROM cadvendedor WHERE situacaoregistro <> 'E' ORDER BY nome")
            ).fetchall()

            vendedores = [{"codigo": str(v._mapping["codigo"]).strip(), "nome": str(v._mapping["nome"]).strip()}
                          for v in vendedores_query]

            # Busca condições de pagamento ativas (Verifique se os nomes das colunas batem com sua tabela cadcondpagamento)
            condicoes_query = db.execute(
                text(
                    "SELECT codigo, descricao, acrescimo, desconto FROM cadcondicaopagamento WHERE situacaoregistro <> 'E' ORDER BY descricao")
            ).fetchall()

            condicoes = [{"codigo": str(c._mapping["codigo"]).strip(),
                          "descricao": str(c._mapping["descricao"]).strip()} for c in condicoes_query]

        return {
            "success": True,
            "vendedores": vendedores,
            "condicoes": condicoes
        }
    except Exception as e:
        import traceback
        print("❌ ERRO AO BUSCAR OPÇÕES DE CONDIÇÕES:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@mov_pedido_router.post("/salvar-cabecalho")
async def salvar_cabecalho(request: Request, token: Optional[str] = Query(None)):
    """
    Rota inteligente de cabeçalho:
    - Se não houver 'numerodocumento', gera um novo número e grava a datalancamento (INSERT).
    - Se já houver 'numerodocumento', atualiza os dados MAS PRESERVA a datalancamento (UPDATE).
    """
    try:
        if not token:
            token = request.query_params.get("token")

        nome_banco = get_nome_banco_por_token(token)
        dados = await request.json()

        empresa = dados.get("empresa", 1)
        numerodocumento = dados.get("numerodocumento")
        codigocliente = dados.get("codigocliente")
        codigovendedor = dados.get("codigovendedor")
        codigocondPagamento = dados.get("codigocondPagamento")

        if not codigocliente:
            return {"success": False, "detail": "Código do cliente não informado."}

        db = get_empresa_session(nome_banco)

        # 1. Busca o nome do cliente
        nomecliente = ""
        cliente_obj = db.execute(
            text("SELECT nome FROM cadcliente WHERE codigo = :codigo AND situacaoregistro <> 'E' LIMIT 1"),
            {"codigo": codigocliente}
        ).fetchone()
        if cliente_obj:
            nomecliente = cliente_obj.nome

        # 2. Verifica se o pedido já existe ou precisa ser criado do zero
        if not numerodocumento:
            # 🚀 CENÁRIO A: Pedido Novo -> GRAVA a datalancamento
            datalancamento = dados.get("datalancamento") or datetime.now().strftime("%Y-%m-%d")

            res_num = db.execute(
                text("SELECT COALESCE(MAX(numerodocumento), 0) + 1 AS proximo FROM movnota WHERE empresa = :empresa"),
                {"empresa": empresa}
            ).fetchone()
            numerodocumento = res_num.proximo

            db.execute(
                text("""
                     INSERT INTO movnota
                     (empresa, numerodocumento, codigocliente, nomecliente, codigovendedor, codigocondPagamento,
                      valorTotal, situacaoRegistro, dataRegistro, datalancamento)
                     VALUES (:empresa, :numerodocumento, :codigocliente, :nomecliente, :codigovendedor,
                             :codigocondPagamento, 0.00, 'A', NOW(), :datalancamento)
                     """),
                {
                    "empresa": empresa,
                    "numerodocumento": numerodocumento,
                    "codigocliente": codigocliente,
                    "nomecliente": nomecliente,
                    "codigovendedor": codigovendedor or "001",
                    "codigocondPagamento": codigocondPagamento or "001",
                    "datalancamento": datalancamento
                }
            )
            mensagem = "Pedido iniciado com sucesso!"

        else:
            # 🔄 CENÁRIO B: Pedido Existente -> NÃO ALTERA a datalancamento
            db.execute(
                text("""
                     UPDATE movnota
                     SET codigocliente       = :codigocliente,
                         nomecliente         = :nomecliente,
                         codigovendedor      = :codigovendedor,
                         codigocondPagamento = :codigocondPagamento
                     WHERE empresa = :empresa
                       AND numerodocumento = :numerodocumento
                     """),
                {
                    "codigocliente": codigocliente,
                    "nomecliente": nomecliente,
                    "codigovendedor": codigovendedor,
                    "codigocondPagamento": codigocondPagamento,
                    "empresa": empresa,
                    "numerodocumento": numerodocumento
                }
            )

            # Atualiza os itens com as informações de cliente/vendedor
            db.execute(
                text("""
                     UPDATE movnotaitem
                     SET codigocliente  = :codigocliente,
                         codigovendedor = :codigovendedor
                     WHERE empresa = :empresa
                       AND numerodocumento = :numerodocumento
                     """),
                {
                    "codigocliente": codigocliente,
                    "codigovendedor": codigovendedor,
                    "empresa": empresa,
                    "numerodocumento": numerodocumento
                }
            )
            mensagem = "Cabeçalho atualizado com sucesso!"

        db.commit()
        db.close()

        return {
            "success": True,
            "message": mensagem,
            "numerodocumento": numerodocumento,
            "empresa": empresa,
            "codigocliente": codigocliente,
            "nomecliente": nomecliente,
            "codigovendedor": codigovendedor,
            "codigocondPagamento": codigocondPagamento
        }

    except Exception as e:
        print(f"Erro na rota salvar-cabecalho: {e}")
        return {"success": False, "detail": str(e)}


@mov_pedido_router.post("/recalcular-condicao-pagamento")
async def recalcular_condicao_pagamento(dados: dict, token: str = Query(...)):
    nome_banco = get_nome_banco_por_token(token)
    if not nome_banco:
        raise HTTPException(status_code=403, detail="Token inválido")

    session_empresa = get_empresa_session(nome_banco)
    with session_empresa as db:
        try:
            empresa = int(dados.get("empresa", 1))
            numerodocumento = int(dados.get("numerodocumento", 0))
            codigocondPagamento = str(dados.get("codigocondPagamento") or "").strip()

            if not numerodocumento or not codigocondPagamento:
                raise HTTPException(status_code=400, detail="Documento e condição de pagamento são obrigatórios.")

            # 📌 1. Busca os percentuais da Nova Condição de Pagamento
            sql_cond = text("""
                SELECT acrescimo, desconto
                FROM cadcondicaopagamento
                WHERE TRIM(codigo) = :codigo
                  AND (situacaoregistro IS NULL OR situacaoregistro <> 'E') 
                LIMIT 1
            """)
            cond_data = db.execute(sql_cond, {"codigo": codigocondPagamento}).mappings().fetchone()

            # Lê as colunas corretas do seu banco ('desconto' e 'acrescimo')
            perc_desconto_cond = float(cond_data["desconto"] or 0) if cond_data else 0.0
            perc_acrescimo_cond = float(cond_data["acrescimo"] or 0) if cond_data else 0.0

            logging.info(
                f"📊 Condição {codigocondPagamento} - Desc: {perc_desconto_cond}% | Acrés: {perc_acrescimo_cond}%"
            )

            # 📌 2. Atualiza a nova condição no cabeçalho do pedido (movnota)
            sql_update_cab = text("""
                UPDATE movnota
                SET codigocondPagamento = :cond
                WHERE empresa = :empresa
                  AND numerodocumento = :numerodocumento
            """)
            db.execute(sql_update_cab, {
                "cond": codigocondPagamento,
                "empresa": empresa,
                "numerodocumento": numerodocumento
            })

            # 📌 3. Busca todos os itens ATIVOS do pedido (situacaoregistro <> 'E')
            sql_itens = text("""
                SELECT seq, codigoproduto, quantidade, valorunitariovenda, valorDesconto, valoracrescimo
                FROM movnotaitem
                WHERE empresa = :empresa
                  AND numerodocumento = :numerodocumento
                  AND (situacaoregistro IS NULL OR situacaoregistro <> 'E')
            """)
            itens_banco = db.execute(sql_itens, {
                "empresa": empresa,
                "numerodocumento": numerodocumento
            }).mappings().all()

            novo_total_pedido = 0.0

            # 📌 4. Recalcula os valores de cada item
            for item in itens_banco:
                seq = item["seq"]
                qtd = float(item["quantidade"] or 0)
                # Base de cálculo do preço de tabela
                vlr_base_venda = float(item["valorunitariovenda"] or 0)

                # Descontos e acréscimos pontuais gravados anteriormente no item
                desc_item = float(item["valorDesconto"] or 0)
                acres_item = float(item["valoracrescimo"] or 0)

                # A. Aplica o percentual da condição de pagamento sobre a base da tabela
                vlr_cond_desconto = (vlr_base_venda * (perc_desconto_cond / 100.0))
                vlr_cond_acrescimo = (vlr_base_venda * (perc_acrescimo_cond / 100.0))

                # B. Descobre o novo valor unitário negociado (arredondado para 2 casas)
                novo_valor_unitario = round(vlr_base_venda - vlr_cond_desconto + vlr_cond_acrescimo, 2)

                # C. Calcula o valor total do item considerando o histórico de desconto e acréscimo do item
                vlr_bruto_item = novo_valor_unitario * qtd
                novo_valor_total_item = round(max(0.0, vlr_bruto_item - desc_item + acres_item), 2)

                # D. Soma ao total geral do pedido
                novo_total_pedido += novo_valor_total_item

                # E. Atualiza o item na tabela movnotaitem com 2 casas
                sql_update_item = text("""
                    UPDATE movnotaitem
                    SET valorUnitario = :val_unit,
                        valorTotal    = :val_total
                    WHERE empresa = :empresa
                      AND numerodocumento = :numerodocumento
                      AND seq = :seq
                """)
                db.execute(sql_update_item, {
                    "val_unit": novo_valor_unitario,
                    "val_total": novo_valor_total_item,
                    "empresa": empresa,
                    "numerodocumento": numerodocumento,
                    "seq": seq
                })

            # Arredonda o acumulador final por segurança de precisão
            novo_total_pedido = round(novo_total_pedido, 2)

            # 📌 5. Atualiza o Total Geral do Pedido no Cabeçalho (movnota)
            sql_update_nota_total = text("""
                UPDATE movnota
                SET valorTotal = :total
                WHERE empresa = :empresa
                  AND numerodocumento = :numerodocumento
            """)
            db.execute(sql_update_nota_total, {
                "total": novo_total_pedido,
                "empresa": empresa,
                "numerodocumento": numerodocumento
            })

            db.commit()

            return {
                "success": True,
                "message": "Condição de pagamento alterada e valores recalculados com sucesso!",
                "numerodocumento": numerodocumento,
                "novoValorTotal": novo_total_pedido
            }

        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            import traceback
            traceback.print_exc()
            logging.error("❌ Erro ao recalcular condição de pagamento: %s", str(e))
            raise HTTPException(status_code=500, detail=f"Erro ao recalcular condição: {str(e)}")

@mov_pedido_router.post("/remover-item")
async def remover_item_pedido(dados: dict, token: str = Query(...)):
    nome_banco = get_nome_banco_por_token(token)
    if not nome_banco:
        raise HTTPException(status_code=403, detail="Token inválido")

    session_empresa = get_empresa_session(nome_banco)
    with session_empresa as db:
        try:
            # 📌 1. Captura e higienização dos parâmetros
            empresa = int(dados.get("empresa", 1))
            numerodocumento = int(dados.get("numerodocumento", 0))
            codigoproduto = str(dados.get("codigoproduto") or "").strip()

            # Trata o campo seq (converte para int se existir)
            raw_seq = dados.get("seq")
            seq = int(raw_seq) if raw_seq not in [None, "", "undefined", "null"] else None

            if not numerodocumento or not codigoproduto:
                raise HTTPException(status_code=400, detail="Número do documento e código do produto são obrigatórios.")

            # 📌 2. Monta consulta flexível com TRIM para ignorar espaços em CHAR(6)
            sql_busca_item = """
                             SELECT seq, codigoproduto, valorTotal
                             FROM movnotaitem
                             WHERE empresa = :empresa
                               AND numerodocumento = :numerodocumento
                               AND TRIM(codigoproduto) = :codigoproduto
                               AND (situacaoregistro IS NULL OR situacaoregistro <> 'E') \
                             """
            params = {
                "empresa": empresa,
                "numerodocumento": numerodocumento,
                "codigoproduto": codigoproduto
            }

            # Se a sequência foi enviada e for maior que 0, adiciona na busca
            if seq and seq > 0:
                sql_busca_item += " AND seq = :seq"
                params["seq"] = seq

            sql_busca_item += " LIMIT 1"

            item_banco = db.execute(text(sql_busca_item), params).mappings().fetchone()

            # Caso ainda não encontre com seq exato, faz o fallback buscando apenas pelo codigoproduto
            if not item_banco and seq:
                sql_fallback = """
                               SELECT seq, codigoproduto, valorTotal
                               FROM movnotaitem
                               WHERE empresa = :empresa
                                 AND numerodocumento = :numerodocumento
                                 AND TRIM(codigoproduto) = :codigoproduto
                                 AND (situacaoregistro IS NULL OR situacaoregistro <> 'E') LIMIT 1 \
                               """
                item_banco = db.execute(text(sql_fallback), {
                    "empresa": empresa,
                    "numerodocumento": numerodocumento,
                    "codigoproduto": codigoproduto
                }).mappings().fetchone()

            # Se mesmo assim não achar nada no banco, aí sim retorna 404
            if not item_banco:
                logging.warning(f"⚠️ Item não localizado. Params: {params}")
                raise HTTPException(status_code=404,
                                    detail=f"Produto {codigoproduto} não encontrado no pedido {numerodocumento}.")

            seq_encontrado = item_banco["seq"]
            cod_produto_encontrado = item_banco["codigoproduto"]
            valor_total_item = float(item_banco["valorTotal"] or 0)

            # 📌 3. Soft Delete na tabela movnotaitem (situacaoregistro = 'E')
            sql_cancelar_item = text("""
                                     UPDATE movnotaitem
                                     SET situacaoregistro = 'E'
                                     WHERE empresa = :empresa
                                       AND numerodocumento = :numerodocumento
                                       AND seq = :seq
                                     """)
            db.execute(sql_cancelar_item, {
                "empresa": empresa,
                "numerodocumento": numerodocumento,
                "seq": seq_encontrado
            })

            # 📌 4. Atualiza e subtrai o valor no total do pedido (movnota)
            sql_update_nota = text("""
                                   UPDATE movnota
                                   SET valorTotal = GREATEST(0, COALESCE(valorTotal, 0) - :valor_item)
                                   WHERE empresa = :empresa
                                     AND numerodocumento = :numerodocumento
                                   """)
            db.execute(sql_update_nota, {
                "valor_item": valor_total_item,
                "empresa": empresa,
                "numerodocumento": numerodocumento
            })

            db.commit()

            return {
                "success": True,
                "message": f"Produto {codigoproduto} removido com sucesso!",
                "numerodocumento": numerodocumento,
                "codigoproduto": codigoproduto,
                "seq": seq_encontrado
            }

        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            import traceback
            traceback.print_exc()
            logging.error("❌ Erro ao remover item do pedido: %s", str(e))
            raise HTTPException(status_code=500, detail=f"Erro ao remover item: {str(e)}")