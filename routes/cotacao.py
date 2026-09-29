from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from typing import Optional
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.sql import text
from database.dependencies import get_empresa_db, get_nome_banco_por_token
from database.connection import get_empresa_session, DB_CHAVE
from datetime import datetime, date
from math import ceil
from urllib.parse import urlencode
from fastapi import Query


cotacao_router = APIRouter()

templates = Jinja2Templates(directory="templates")
templates.env.globals['now'] = datetime.now


@cotacao_router.get("/", response_class=HTMLResponse)
async def listar_cotacoes(
    request: Request,
    cliente: Optional[str] = Query(None),
    vendedor: Optional[str] = Query(None),
    item: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=10, le=100)
):
    empresa_token = request.cookies.get("empresa_token")
    empresa_cnpj = request.cookies.get("empresa_cnpj")
    usuario_id = request.cookies.get("usuario_id")

    if not empresa_token or not empresa_cnpj or not usuario_id:
        return RedirectResponse("/login-usuario", status_code=303)

    nome_banco = get_nome_banco_por_token(empresa_token)

    if not nome_banco:
        raise HTTPException(
            status_code=403,
            detail="Empresa não encontrada."
        )

    session_empresa = get_empresa_session(nome_banco)

    cotacoes = []
    total_registros = 0

    hoje = datetime.now().strftime("%Y-%m-%d")

    data_inicio = (
        data_inicio.strip()
        if data_inicio and data_inicio.strip()
        else hoje
    )

    data_fim = (
        data_fim.strip()
        if data_fim and data_fim.strip()
        else hoje
    )

    if data_inicio > data_fim:
        data_inicio, data_fim = data_fim, data_inicio

    data_inicio_sql = f"{data_inicio} 00:00:00"
    data_fim_sql = f"{data_fim} 23:59:59"

    with session_empresa as db:
        usuario = db.execute(
            text("""
                SELECT
                    id,
                    empresa,
                    codigovendedor,
                    usuario
                FROM cadusers
                WHERE id = :usuario_id
                  AND situacaoregistro <> 'E'
                LIMIT 1
            """),
            {"usuario_id": usuario_id}
        ).mappings().first()

        if not usuario:
            return RedirectResponse("/login-usuario", status_code=303)

        empresa = usuario["empresa"]

        filtros = [
            "mn.empresa = :empresa",
            "mni.tipodocumento = 'COTACAO'",
            "mni.situacaoregistro <> 'E'",
            "mn.situacaoregistro <> 'E'",
            "mn.dataLancamento BETWEEN :data_inicio AND :data_fim"
        ]

        parametros = {
            "empresa": empresa,
            "data_inicio": data_inicio_sql,
            "data_fim": data_fim_sql
        }

        if cliente:
            cliente = cliente.strip()

            if cliente:
                filtros.append("""
                    (
                        mn.codigocliente = :cliente
                        OR mn.nomecliente LIKE :cliente_like
                    )
                """)

                parametros["cliente"] = cliente
                parametros["cliente_like"] = f"%{cliente}%"

        if vendedor:
            vendedor = vendedor.strip()

            if vendedor:
                filtros.append("""
                    (
                        mn.codigovendedor = :vendedor
                        OR V.nome LIKE :vendedor_like
                    )
                """)

                parametros["vendedor"] = vendedor
                parametros["vendedor_like"] = f"%{vendedor}%"

        if item:
            item = item.strip()

            if item:
                filtros.append("""
                    (
                        mni.codigoproduto = :item
                        OR mni.descricaoproduto LIKE :item_like
                    )
                """)

                parametros["item"] = item
                parametros["item_like"] = f"%{item}%"

        where_sql = " AND ".join(filtros)

        # Total de registros para a paginação.
        total_query = db.execute(
            text(f"""
                SELECT COUNT(*)
                FROM movnota mn
                INNER JOIN movnotaitem mni
                    ON mni.movnota_id = mn.id
                LEFT JOIN cadvendedor V
                    ON V.codigo = mn.codigovendedor
                   AND V.empresa = mn.empresa
                WHERE {where_sql}
            """),
            parametros
        )

        total_registros = total_query.scalar() or 0

        total_paginas = max(
            1,
            ceil(total_registros / por_pagina)
        )

        if pagina > total_paginas:
            pagina = total_paginas

        offset = (pagina - 1) * por_pagina

        # Registros da página atual.
        cotacoes_query = db.execute(
            text(f"""
                SELECT
                    mn.id AS movnota_id,
                    mn.numerodocumento,
                    mn.codigocliente,
                    mn.nomecliente,
                    mn.codigovendedor,
                    mn.dataLancamento,
                    mni.seq,
                    mni.codigoproduto,
                    mni.descricaoproduto,
                    mni.quantidade,
                    mni.quantidade_pedida,
                    (
                        mni.quantidade -
                        mni.quantidade_pedida
                    ) AS quantidade_saldo,
                    mni.valorUnitario,
                    mni.valorTotal
                FROM movnota mn
                INNER JOIN movnotaitem mni
                    ON mni.movnota_id = mn.id
                LEFT JOIN cadvendedor V
                    ON V.codigo = mn.codigovendedor
                   AND V.empresa = mn.empresa
                WHERE {where_sql}
                ORDER BY
                    mn.numerodocumento DESC,
                    mni.seq
                LIMIT :limite
                OFFSET :offset
            """),
            {
                **parametros,
                "limite": por_pagina,
                "offset": offset
            }
        ).mappings().all()

        cotacoes = list(cotacoes_query)

    registro_inicio = (
        offset + 1
        if total_registros > 0
        else 0
    )

    registro_fim = min(
        offset + por_pagina,
        total_registros
    )

    # Gera as páginas mantendo os filtros.
    def url_paginacao(numero):
        parametros_url = {
            "pagina": numero,
            "por_pagina": por_pagina,
            "data_inicio": data_inicio,
            "data_fim": data_fim
        }

        if cliente:
            parametros_url["cliente"] = cliente

        if vendedor:
            parametros_url["vendedor"] = vendedor

        if item:
            parametros_url["item"] = item

        return "/cotacao/?" + urlencode(parametros_url)

    # Exibe no máximo 5 páginas próximas da atual.
    paginas = []

    inicio_paginas = max(1, pagina - 2)
    fim_paginas = min(total_paginas, pagina + 2)

    if inicio_paginas > 1:
        paginas.append(1)

        if inicio_paginas > 2:
            paginas.append("...")

    paginas.extend(
        range(
            inicio_paginas,
            fim_paginas + 1
        )
    )

    if fim_paginas < total_paginas:
        if fim_paginas < total_paginas - 1:
            paginas.append("...")

        paginas.append(total_paginas)

    return templates.TemplateResponse(
        "cotacao/listar_cotacao.html",
        {
            "request": request,
            "empresa": empresa,
            "empresa_cnpj": empresa_cnpj,
            "empresa_token": empresa_token,
            "usuario_id": usuario_id,
            "cotacoes": cotacoes,

            # Filtros
            "cliente": cliente,
            "vendedor": vendedor,
            "item": item,
            "data_inicio": data_inicio,
            "data_fim": data_fim,

            # Paginação
            "pagina": pagina,
            "por_pagina": por_pagina,
            "total_registros": total_registros,
            "total_paginas": total_paginas,
            "registro_inicio": registro_inicio,
            "registro_fim": registro_fim,
            "paginas": paginas,
            "url_paginacao": url_paginacao
        }
    )


@cotacao_router.post("/faturar-item")
async def faturar_item_cotacao(
    request: Request,
    numerodocumento: int,
    seq: int
):
    empresa_token = request.cookies.get("empresa_token")
    empresa_cnpj = request.cookies.get("empresa_cnpj")
    usuario_id = request.cookies.get("usuario_id")

    if not empresa_token or not empresa_cnpj or not usuario_id:
        raise HTTPException(
            status_code=401,
            detail="Usuário não autenticado."
        )

    nome_banco = get_nome_banco_por_token(empresa_token)
    if not nome_banco:
        raise HTTPException(
            status_code=403,
            detail="Empresa não encontrada."
        )

    session_empresa = get_empresa_session(nome_banco)

    with session_empresa as db:
        try:
            usuario = db.execute(
                text("""
                    SELECT id, empresa
                    FROM cadusers
                    WHERE id = :usuario_id
                      AND situacaoregistro <> 'E'
                    LIMIT 1
                """),
                {"usuario_id": usuario_id}
            ).mappings().first()

            if not usuario:
                raise HTTPException(
                    status_code=401,
                    detail="Usuário não encontrado."
                )

            empresa = usuario["empresa"]

            item = db.execute(
                text("""
                    SELECT
                        quantidade,
                        quantidade_pedida,
                        tipodocumento
                    FROM movnotaitem
                    WHERE empresa = :empresa
                      AND numerodocumento = :numerodocumento
                      AND seq = :seq
                      AND situacaoRegistro <> 'E'
                    LIMIT 1
                """),
                {
                    "empresa": empresa,
                    "numerodocumento": numerodocumento,
                    "seq": seq
                }
            ).mappings().first()

            if not item:
                raise HTTPException(
                    status_code=404,
                    detail="Item da cotação não encontrado."
                )

            if str(item["tipodocumento"] or "").upper() != "COTACAO":
                raise HTTPException(
                    status_code=400,
                    detail="Este item não está mais em cotação."
                )

            quantidade = float(item["quantidade"] or 0)
            quantidade_pedida = float(item["quantidade_pedida"] or 0)
            saldo = quantidade - quantidade_pedida

            if saldo <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Este item não possui quantidade disponível para faturar."
                )

            db.execute(
                text("""
                    UPDATE movnotaitem
                    SET
                        tipodocumento = 'PEDIDO',
                        quantidade_pedida = quantidade
                    WHERE empresa = :empresa
                      AND numerodocumento = :numerodocumento
                      AND seq = :seq
                      AND tipodocumento = 'COTACAO'
                      AND situacaoRegistro <> 'E'
                """),
                {
                    "empresa": empresa,
                    "numerodocumento": numerodocumento,
                    "seq": seq
                }
            )

            db.commit()

            return {
                "sucesso": True,
                "mensagem": "Item faturado com sucesso.",
                "numerodocumento": numerodocumento,
                "seq": seq,
                "quantidade": quantidade,
                "tipodocumento": "PEDIDO"
            }

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao faturar item: {str(e)}"
            )


@cotacao_router.post("/faturar-todos")
async def faturar_todos_cotacao(
    request: Request,
    numerodocumento: int
):
    empresa_token = request.cookies.get("empresa_token")
    empresa_cnpj = request.cookies.get("empresa_cnpj")
    usuario_id = request.cookies.get("usuario_id")

    if not empresa_token or not empresa_cnpj or not usuario_id:
        raise HTTPException(
            status_code=401,
            detail="Usuário não autenticado."
        )

    nome_banco = get_nome_banco_por_token(empresa_token)
    if not nome_banco:
        raise HTTPException(
            status_code=403,
            detail="Empresa não encontrada."
        )

    session_empresa = get_empresa_session(nome_banco)

    with session_empresa as db:
        try:
            usuario = db.execute(
                text("""
                    SELECT id, empresa
                    FROM cadusers
                    WHERE id = :usuario_id
                      AND situacaoregistro <> 'E'
                    LIMIT 1
                """),
                {"usuario_id": usuario_id}
            ).mappings().first()

            if not usuario:
                raise HTTPException(
                    status_code=401,
                    detail="Usuário não encontrado."
                )

            empresa = usuario["empresa"]

            resultado = db.execute(
                text("""
                    SELECT COUNT(*) AS total
                    FROM movnotaitem
                    WHERE empresa = :empresa
                      AND numerodocumento = :numerodocumento
                      AND tipodocumento = 'COTACAO'
                      AND situacaoRegistro <> 'E'
                """),
                {
                    "empresa": empresa,
                    "numerodocumento": numerodocumento
                }
            ).mappings().first()

            total = int(resultado["total"] or 0)

            if total == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Não existem itens em cotação para faturar."
                )

            resultado_update = db.execute(
                text("""
                    UPDATE movnotaitem
                    SET
                        tipodocumento = 'PEDIDO',
                        quantidade_pedida = quantidade
                    WHERE empresa = :empresa
                      AND numerodocumento = :numerodocumento
                      AND tipodocumento = 'COTACAO'
                      AND situacaoRegistro <> 'E'
                """),
                {
                    "empresa": empresa,
                    "numerodocumento": numerodocumento
                }
            )

            db.commit()

            return {
                "sucesso": True,
                "mensagem": "Todos os itens da cotação foram faturados.",
                "numerodocumento": numerodocumento,
                "quantidade_itens": resultado_update.rowcount,
                "tipodocumento": "PEDIDO"
            }

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao faturar cotação: {str(e)}"
            )