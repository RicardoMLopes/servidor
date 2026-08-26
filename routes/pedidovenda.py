from io import BytesIO
import logging
import os
import pdfkit
from fastapi import APIRouter, Depends, Form, Request
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


pedido_router = APIRouter()
pedido_relatorios_router = APIRouter()
pedido_relatorios_PDF_router = APIRouter()
resumomensal_router = APIRouter()

templates = Jinja2Templates(directory="templates")
templates.env.globals['now'] = datetime.now
templates.env.filters['moeda_br'] = moeda_br


def gerar_pdf_relatorio(relatorio, tipo="analitico", template_path=None, empresa=None) -> BytesIO:
    """
    Gera PDF a partir de dados de relatório com header e rodapé com número de página.

    :param relatorio: lista de dicionários com os dados do relatório
    :param tipo: tipo de relatório ("analitico" ou "sintetico")
    :param template_path: caminho do template HTML principal (opcional)
    :param empresa: dicionário com dados da empresa {"nome": ..., "cnpj": ..., "telefone": ...}
    :return: BytesIO com o PDF gerado
    """

    # Detecta wkhtmltopdf
    wkhtmltopdf_path = shutil.which("wkhtmltopdf")
    if not wkhtmltopdf_path:
        raise RuntimeError("wkhtmltopdf não encontrado no PATH. Instale-o e/ou adicione ao PATH.")

    config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

    # Caminho padrão do template
    if template_path is None:
        template_dir = os.path.join(os.getcwd(), "templates")
        template_name = "pedido/relatorio_pedido_pdf.html"
    else:
        template_dir = os.path.dirname(template_path)
        template_name = os.path.basename(template_path)

    # Verifica se o template existe
    full_template_path = os.path.join(template_dir, template_name)
    if not os.path.exists(full_template_path):
        raise FileNotFoundError(f"Template não encontrado: {full_template_path}")

    # Normaliza campo dataLancamento_html
    for p in relatorio:
        cabecalho = p.get("cabecalho", {})

        data_raw = cabecalho.get("datalancamento")
      #  logging.warning("DATA LANCAMENTO: %s", data_raw)
        # Tenta converter a data se for string válida
        if isinstance(data_raw, (datetime, date)):
            data_formatada = data_raw.strftime("%d/%m/%Y")
        else:
            try:
                # Ignora strings vazias ou nulas
                if data_raw and str(data_raw).strip():
                    data_obj = parse(str(data_raw))
                    data_formatada = data_obj.strftime("%d/%m/%Y")
                else:
                    data_formatada = "—"  # Placeholder para datas ausentes
            except Exception as e:
                logging.warning("Erro ao converter dataLancamento: %s", e)
                data_formatada = "—"

        cabecalho["dataLancamento_html"] = data_formatada
        p["cabecalho"] = cabecalho  # Garante que a alteração reflita no objeto principal

    # Ambiente Jinja
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)

    # Renderiza template principal
    main_template = env.get_template(template_name)
    html_rendered = main_template.render(
        tipo=tipo,
        relatorio=relatorio,
        empresa=empresa or {},
        data_atual=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    )

    # Salva HTML principal em arquivo temporário
    temp_main = tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8")
    temp_main.write(html_rendered)
    temp_main.close()

    # Configurações PDF com rodapé nativo
    options = {
        'page-size': 'A4',
        'margin-top': '20mm',
        'margin-right': '15mm',
        'margin-bottom': '20mm',
        'margin-left': '15mm',
        'encoding': 'UTF-8',
        'footer-left': 'desenvolvedora: Data Access Informática Ltda - Tel: (31) 3771-8273 site: https://dataaccess.inf.br/',
        'footer-right': 'Página [page] de [topage]',
        'footer-line': True,
        'footer-font-size': '9'
    }

    # Gera PDF usando arquivo temporário
    pdf_bytes = pdfkit.from_file(
        temp_main.name,
        False,
        configuration=config,
        options=options
    )

    # Remove arquivo temporário
    os.unlink(temp_main.name)

    return BytesIO(pdf_bytes)

@pedido_router.post("")
async def inserir_pedido_api(nota: dict, db: Session = Depends(get_empresa_db)):

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


def to_float(valor):
    return float(valor or 0)

def to_decimal(valor):
    if valor is None:
        return Decimal("0")
    if isinstance(valor, Decimal):
        return valor
    return Decimal(str(valor))  # Converte float ou int para Decimal


@pedido_relatorios_router.get("/", response_class=HTMLResponse)
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

    # 🔹 Gera token a partir do CNPJ se necessário
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
                "telefone": None,
                "token": token
            }
        )

    nome_banco = get_nome_banco_por_token(token)
    if not nome_banco:
        raise HTTPException(status_code=403, detail="Token inválido ou empresa não encontrada")

    db = get_empresa_session(nome_banco)
    empresa_war = ConsultaEmpresa(db)
    codigo_empresa = int(str(empresa_war[0]).lstrip("0"))
    empresa_cnpj = str(empresa_war[2]) if len(empresa_war) > 1 else ""
    nome_empresa = str(empresa_war[1]) if len(empresa_war) > 1 else "Empresa"
    telefone_empresa = str(empresa_war[7]) if len(empresa_war) > 7 else ""

    try:
        numerodocumento = int(numerodocumento) if numerodocumento else None
    except ValueError:
        numerodocumento = None


    filtros = ["A.empresa = :empresa"]
    filtros.append("(B.situacaoregistro IS NULL OR B.situacaoregistro <> 'E')")
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
                "cnpj": empresa_cnpj,
                "telefone": telefone_empresa,
                "token": token
            }
        )

    where_clause = " AND ".join(filtros)

    sql = f"""
        SELECT A.numerodocumento, A.codigovendedor, V.nome as nomevendedor, A.codigocliente, A.nomecliente, A.dataLancamento,
               A.codigocondPagamento, F.descricao as formapagamento, A.status, A.observacao,
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

    pedidos = db.execute(text(sql), parametros).fetchall()

    # ===================== SINTÉTICO =====================
    if tipo == "sintetico":
        pedidos_dict_sintetico = {}
        for p in pedidos:
            numdoc = p._mapping["numerodocumento"]

            if numdoc not in pedidos_dict_sintetico:
                data_raw = p._mapping.get("dataLancamento")
                try:
                    if data_raw and str(data_raw).strip():
                        data_obj = parse(str(data_raw))
                        data_lancamento_html = data_obj.strftime("%d/%m/%Y %H:%M:%S")
                    else:
                        data_lancamento_html = "—"
                except Exception:
                    data_lancamento_html = "—"

                pedidos_dict_sintetico[numdoc] = {
                    "cabecalho": {
                        "numerodocumento": numdoc,
                        "nomecliente": p._mapping["nomecliente"],
                        "codigovendedor": p._mapping["codigovendedor"],
                        "nomevendedor": p._mapping["nomevendedor"],
                        "observacao": p._mapping["observacao"],
                        "dataLancamento_html": data_lancamento_html,
                        "formapagamento": p._mapping.get("formapagamento") or "",
                        "status": p._mapping["status"],
                    },
                    "totalizadores": {
                        "subtotal": 0.0,
                        "totalDesconto": 0.0,
                        "totalAcrescimo": 0.0,
                        "totalGeral": 0.0,
                        "qtd_itens": 0,
                    },
                }

            # 🔹 Arredondamento antes do cálculo
            preco = round(to_float(p._mapping.get("valorunitariovenda", 0)), 2)
            quant = round(to_float(p._mapping.get("quantidade", 0)), 2)
            desconto = round(to_float(p._mapping.get("valorDesconto", 0)), 2)
            acresc = round(to_float(p._mapping.get("valoracrescimo", 0)), 2)
            total = round(to_float(p._mapping.get("valorTotal", 0)), 2)

            tot = pedidos_dict_sintetico[numdoc]["totalizadores"]
            tot["subtotal"] += round(preco * quant, 2)
            tot["totalDesconto"] += desconto
            tot["totalAcrescimo"] += acresc
            tot["totalGeral"] += total
            tot["qtd_itens"] += quant

        relatorio = list(pedidos_dict_sintetico.values())

    # ===================== ANALÍTICO =====================
    else:
        pedidos_dict = {}
        for p in pedidos:
            numdoc = p._mapping["numerodocumento"]

            if numdoc not in pedidos_dict:
                cabecalho = dict(p._mapping)
                if isinstance(cabecalho.get("dataLancamento"), datetime):
                    cabecalho["dataLancamento_html"] = cabecalho["dataLancamento"].strftime("%d/%m/%Y %H:%M:%S")
                else:
                    cabecalho["dataLancamento_html"] = cabecalho.get("dataLancamento", "")
                for key in ["valorunitariovenda", "valorDesconto", "valoracrescimo", "valorTotal"]:
                    if key in cabecalho and isinstance(cabecalho[key], Decimal):
                        cabecalho[key] = float(cabecalho[key])

                pedidos_dict[numdoc] = {
                    "cabecalho": cabecalho,
                    "itens": [],
                    "totalizadores": {"totalDesconto": 0, "totalAcrescimo": 0, "totalGeral": 0, "subtotal": 0.0},
                }

            preco = round(to_float(p._mapping.get("valorunitariovenda", 0)), 2)
            quant = round(to_float(p._mapping.get("quantidade", 0)), 2)
            desconto = round(to_float(p._mapping.get("valorDesconto", 0)), 2)
            acresc = round(to_float(p._mapping.get("valoracrescimo", 0)), 2)
            total = round(to_float(p._mapping.get("valorTotal", 0)), 2)

            pedidos_dict[numdoc]["itens"].append({
                "codigoproduto": p._mapping["codigoproduto"],
                "descricaoproduto": p._mapping["descricaoproduto"],
                "quantidade": quant,
                "valorunitariovenda": preco,
                "valorDesconto": desconto,
                "valoracrescimo": acresc,
                "valorTotal": total
            })

            tot = pedidos_dict[numdoc]["totalizadores"]
            tot["subtotal"] += round(preco * quant, 2)
            tot["totalDesconto"] += desconto
            tot["totalAcrescimo"] += acresc
            tot["totalGeral"] += total

        relatorio = list(pedidos_dict.values())

    # 🔹 Converte para JSON serializável
    relatorio_serializavel = make_json_serializable(relatorio)

    # 🔹 Cálculo de status_count
    status_count = {"P": 0, "R": 0}
    for pedido in relatorio_serializavel:
        status_val = pedido.get("cabecalho", {}).get("status")
        if status_val in status_count:
            status_count[status_val] += 1

    return templates.TemplateResponse(
        "pedido/relatorio_pedido.html",
        {
            "request": request,
            "relatorio": relatorio_serializavel,
            "tipo": tipo,
            "empresa_nome": nome_empresa,
            "cliente": "",
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "numerodocumento": "",
            "agrupamento": "",
            "status": status,
            "cnpj": empresa_cnpj,
            "telefone": telefone_empresa,
            "token": token,
            "status_count": status_count
        }
    )


# ==========================================================================================|
#                   RELATÓRIO -  GERAÇÃO DO PEDIDO DE VENDA                                 |
#===========================================================================================|


# Função utilitária para serializar datetime/Decimal
def make_json_serializable(obj):
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(v) for v in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    elif obj is None:
        return None
    else:
        return obj


@pedido_relatorios_PDF_router.post("/")
async def relatorio_pedido_pdf(request: Request, payload: dict):
    """
    Recebe JSON do front-end e retorna PDF gerado do template HTML.
    Espera payload no formato:
    {
        "tipo": "analitico" | "sintetico",
        "relatorio": [...],
        "empresa": {
            "nome": "...",
            "cnpj": "...",
            "telefone": "..."
        }
    }
    """
 #   logging.warning("Payload PDF: %s", payload)

    tipo: str = payload.get("tipo", "analitico")
    relatorio: list = payload.get("relatorio", [])
    empresa_dict: Optional[dict] = payload.get("empresa", {})

    if not relatorio:
        return {"erro": "Nenhum dado de relatório fornecido."}


    # Torna os dados serializáveis caso use Decimal ou datas
    relatorio_serializavel = make_json_serializable(relatorio)

    # Prepara relatório (formata datas, forma de pagamento, etc.)
    relatorio_formatado = preparar_relatorio_para_pdf(relatorio_serializavel)

    # Gera PDF
    pdf_io: BytesIO = gerar_pdf_relatorio(
        relatorio=relatorio_formatado,
        tipo=tipo,
        empresa=empresa_dict
    )

    # Retorna PDF como attachment
    filename = f"relatorio_{tipo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return StreamingResponse(
        pdf_io,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )




def preparar_relatorio_para_pdf(relatorio):
    relatorio_formatado = []

    for p in relatorio:
        # Formata a data
        data_br = ""
        if p.get("cabecalho", {}).get("dataLancamento"):
            dt = datetime.fromisoformat(p["cabecalho"]["dataLancamento"].replace("Z", "+00:00"))
            data_br = dt.strftime("%d/%m/%Y %H:%M:%S")

        # Forma de pagamento
        forma_pagamento = ""
        if p.get("cabecalho"):
            codigo = p["cabecalho"].get("codigocondPagamento", "")
            descricao = p["cabecalho"].get("formapagamento", "")
            forma_pagamento = f"{codigo} - {descricao}" if codigo else descricao

        # Copia o restante dos dados
        item_formatado = p.copy()
        item_formatado["cabecalho"]["dataLancamento"] = data_br
        item_formatado["cabecalho"]["formaPagamento"] = forma_pagamento

        relatorio_formatado.append(item_formatado)

    return relatorio_formatado


# =========================
# 📄 VIEW (abre a tela HTML)
# =========================


@resumomensal_router.api_route(
    "/view",
    methods=["GET", "POST"],
    response_class=HTMLResponse
)
async def view_resumo_mensal(request: Request):

    try:
        print("\n========== RESUMO MENSAL ==========")

        # 🔹 identifica método
        metodo = request.method
        print(f"[0] Método: {metodo}")

        # 🔹 se for POST → pega do form
        if metodo == "POST":
            form = await request.form()
            cnpj = form.get("cnpj")
        else:
            # 🔹 se for GET → pega da query (opcional)
            cnpj = request.query_params.get("cnpj")

        print(f"[1] CNPJ recebido: {cnpj}")

        # 🔹 se não tem CNPJ → só abre tela
        if not cnpj:
            print("[INFO] Abrindo tela vazia")
            return templates.TemplateResponse(
                "pedido/resumomensal.html",
                {
                    "request": request,
                    "empresa": None,
                    "vendedores": [],
                    "cnpj": ""
                }
            )

        # 🔹 fluxo normal (igual seu)
        token = gerar_token_cnpj(cnpj, DB_CHAVE)
        print(f"[2] Token: {token}")

        nome_banco = get_nome_banco_por_token(token)
        print(f"[3] Banco: {nome_banco}")

        if not nome_banco:
            return HTMLResponse("Banco não encontrado", status_code=400)

        session_empresa = get_empresa_session(nome_banco)

        with session_empresa as db:

            empresa_raw = ConsultaEmpresaPorCNPJ(db, cnpj)
            if not empresa_raw:
                return HTMLResponse("Empresa não encontrada", status_code=404)

            empresa = empresa_raw[0]
            print(f"[4] Empresa: {empresa.get('nome')}")

            vendedores_raw = ConsultaVendedores(db)
            print(f"[5] Vendedores: {len(vendedores_raw)}")

            vendedores = [
                {"id": v["codigo"], "nome": v["nome"]}
                for v in vendedores_raw
            ]

        print("[6] Renderizando template")
        print("===================================\n")

        return templates.TemplateResponse(
            "pedido/resumomensal.html",
            {
                "request": request,
                "empresa": empresa,
                "vendedores": vendedores,
                "cnpj": cnpj
            }
        )

    except Exception as e:
        print("\n❌ ERRO NO RESUMO MENSAL")
        traceback.print_exc()
        return HTMLResponse(f"Erro interno: {str(e)}", status_code=500)
# =========================
# 📊 API (dados financeiros)
# =========================
@resumomensal_router.get("/dados")
def resumo_dados(
    codigovendedor: str,
    cnpj: str
):
    try:
        print("\n====== DADOS RESUMO ======")
        print(f"Vendedor: {codigovendedor}")
        print(f"CNPJ: {cnpj}")

        # 🔹 1. Validar entrada
        if not codigovendedor:
            return JSONResponse({"erro": "Código do vendedor não informado"}, status_code=400)

        if not cnpj:
            return JSONResponse({"erro": "CNPJ não informado"}, status_code=400)

        # 🔹 2. Gerar token
        token = gerar_token_cnpj(cnpj, DB_CHAVE)
        print(f"[TOKEN] {token}")

        # 🔹 3. Descobrir banco
        nome_banco = get_nome_banco_por_token(token)
        print(f"[BANCO] {nome_banco}")

        if not nome_banco:
            return JSONResponse({"erro": "Banco não encontrado"}, status_code=400)

        # 🔹 4. Criar sessão
        session_empresa = get_empresa_session(nome_banco)

        with session_empresa as db:

            # 🔹 5. Data atual
            hoje = datetime.now()
            mes = str(hoje.month).zfill(2)
            ano = str(hoje.year)

            print(f"[PERÍODO] {mes}/{ano}")

            # 🔹 6. Query com limite do vendedor
            result = db.execute(text("""
                SELECT 
                    COALESCE(SUM(i.valorTotal), 0) AS bruto,
                    COALESCE(SUM(i.valorDesconto), 0) + COALESCE(SUM(n.valorDesconto), 0) AS desconto,
                    COALESCE(SUM(i.valoracrescimo), 0) AS acrescimo,
                    MAX(v.limitedesconto) AS limitedesconto
                FROM movnotaitem i
                JOIN movnota n 
                    ON n.numerodocumento = i.numerodocumento
                LEFT JOIN cadvendedor v
                    ON v.codigo = n.codigovendedor
                WHERE DATE_FORMAT(n.dataLancamento, '%m') = :mes
                  AND DATE_FORMAT(n.dataLancamento, '%Y') = :ano
                  AND (n.status IS NULL OR n.status <> 'C')
                  AND n.codigovendedor = :codigovendedor
                  AND n.situacaoregistro <> 'E'  
            """), {
                "mes": mes,
                "ano": ano,
                "codigovendedor": codigovendedor
            }).fetchone()

        # 🔹 7. Garantir retorno seguro
        if not result:
            print("[INFO] Nenhum dado encontrado")
            result = {
                "bruto": 0,
                "desconto": 0,
                "acrescimo": 0,
                "limitedesconto": 0
            }

        # 🔹 8. Conversões seguras
        bruto = float(result.bruto or 0)
        desconto = float(result.desconto or 0)
        acrescimo = float(result.acrescimo or 0)

        # 🔥 percentual do vendedor (do banco)
        percentual_limite = float(result.limitedesconto or 0)

        # 🔹 9. Cálculos
        liquido = bruto - desconto + acrescimo
        percentual_desconto = (desconto / bruto * 100) if bruto > 0 else 0

        limite = bruto * (percentual_limite / 100)
        restante = limite - desconto

        print(f"[BRUTO] {bruto}")
        print(f"[DESCONTO] {desconto}")
        print(f"[ACRESCIMO] {acrescimo}")
        print(f"[LIMITE %] {percentual_limite}")
        print(f"[LIMITE R$] {limite}")
        print(f"[RESTANTE] {restante}")

        print("✔ Dados calculados com sucesso")

        # 🔹 10. Retorno completo
        return {
            "resumo": {
                "bruto": bruto,
                "desconto": desconto,
                "acrescimo": acrescimo,
                "liquido": liquido,
                "percentual_desconto": percentual_desconto,
                "percentual_limite": percentual_limite,
                "limite_desconto": limite,
                "restante_desconto": restante
            }
        }

    except Exception as e:
        print("\n❌ ERRO NO RESUMO")
        traceback.print_exc()

        return JSONResponse(
            {"erro": str(e)},
            status_code=500
        )