import ast
import logging
import os, io
from datetime import datetime
from typing import Optional
import pytz
from fastapi import APIRouter
from fastapi import Query, Request, UploadFile, Form
from starlette.responses import HTMLResponse
from typing import List
from database.connection import get_empresa_session, DB_CHAVE
from function.funtions import gerar_token_cnpj, limpa_cnpj, parse_last_sync
from params.alerta import enviar_alerta
from database.querys import ConsultaProduto, Insert_Produto, ConsultaEmpresa, ConsultarListaProduto
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from database.dependencies import get_empresa_db, get_nome_banco_por_token
import traceback
from fastapi.responses import JSONResponse
import shutil
from PIL import Image
from routes.pedidovenda import templates

products_router = APIRouter()
list_products_router = APIRouter()
upload_imagem_produtos_router = APIRouter()


@products_router.get("")
async def listar_produtos(
    last_sync: Optional[str] = Query(
        None,
        description="Data/hora da última sincronização no formato 'YYYY-MM-DD HH:MM:SS'"
    ),
    db: Session = Depends(get_empresa_db)
):
    logging.warning("ENTROU AQUI")
    try:
        # Validação de formato sem conversão de fuso
        # filtro_data = None
        # if last_sync:
        #     try:
        #         datetime.strptime(last_sync, "%Y-%m-%d %H:%M:%S")
        #         filtro_data = last_sync
        #         logging.warning("DATA RECEBIDA: %s", filtro_data)
        #     except ValueError:
        #         raise HTTPException(status_code=400, detail="Formato inválido para last_sync")

        # Consulta produtos
        dados = ConsultaProduto(db, last_sync)
       # logging.info("PRODUTOS RETORNADOS: %s", len(dados))

        # Hora atual no fuso de São Paulo
        tz_sp = pytz.timezone("America/Sao_Paulo")
        last_sync_servidor = datetime.now(tz_sp).strftime("%Y-%m-%d %H:%M:%S")

        return {
            "produtos": dados,
            "last_sync": last_sync_servidor
        }

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {e.__class__.__name__}: {str(e)}"
        )




@products_router.post("/")
async def atualizar_produto(produto: str, db: Session = Depends(get_empresa_db)):
    try:
        sucesso = Insert_Produto(db, produto)
        if not sucesso:
            raise HTTPException(status_code=400, detail="Erro ao inserir/atualizar produto.")

        return {"mensagem": "Produto inserido/atualizado com sucesso."}

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        enviar_alerta(assunto="Inserção de produtos", mensagem="Erro ao inserir/atualizar produto: " + str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {e.__class__.__name__}: {str(e)}"
        )

# =====================================================================================================================|
#                              LISTAR OS PRODUTOS PARA MANUTENÇÃO
#----------------------------------------------------------------------------------------------------------------------|

UPLOAD_DIR = "static/img"
IMAGEM_PADRAO = "sem_imagem.jpg"

@list_products_router.get("/", response_class=HTMLResponse)
async def produtos_list_template(
    request: Request,
    empresa: Optional[str] = Query(None),
    cnpj: Optional[str] = Query(None),
    token: Optional[str] = Query(None),
    agrupamento: Optional[str] = Query(None),
    descricao: Optional[str] = Query(None),
    codigo: Optional[str] = Query(None),
    codigobarra: Optional[str] = Query(None),
):
    # ------ autenticação / token ------
    if not token and cnpj:
        token = gerar_token_cnpj(cnpj, DB_CHAVE)

    if not token:
        return templates.TemplateResponse(
            "produto/listar_produtos.html",
            {"request": request, "produtos": [], "empresa_nome": None,
             "empresa_cnpj": cnpj, "empresa_token": token}
        )

    nome_banco = get_nome_banco_por_token(token)
    if not nome_banco:
        raise HTTPException(status_code=403, detail="Token inválido ou empresa não encontrada")

    db = get_empresa_session(nome_banco)
    empresa_war = ConsultaEmpresa(db)
    empresa_nome = str(empresa_war[1]) if len(empresa_war) > 1 else "Empresa"

    # ------ pega produtos ------
    resultado = ConsultarListaProduto(db)
    colunas = [
        "empresa","codigo","descricao","unidadeMedida","codigobarra",
        "agrupamento","marca","modelo","tamanho","cor","peso",
        "precovenda","casasdecimais","percentualdesconto","estoque",
        "reajustacondicaopagamento","percentualComissao","situacaoregistro",
        "dataRegistro","versao"
    ]

    produtos = []
    for item in resultado:
        if isinstance(item, dict):
            p = item.copy()
        else:
            if len(item) != len(colunas):
                p = {col: item[i] if i < len(item) else None for i, col in enumerate(colunas)}
            else:
                p = dict(zip(colunas, item))
        produtos.append(p)

    # ------ APLICA FILTROS em Python ------
    descricao_q = descricao.strip().lower() if descricao else None
    agrupamento_q = agrupamento.strip().lower() if agrupamento else None
    codigo_q = codigo.strip().lower() if codigo else None
    codigobarra_q = codigobarra.strip().lower() if codigobarra else None

    if descricao_q:
        produtos = [p for p in produtos if descricao_q in str(p.get("descricao") or "").strip().lower()]
    if agrupamento_q:
        produtos = [p for p in produtos if agrupamento_q in str(p.get("agrupamento") or "").strip().lower()]
    if codigo_q:
        produtos = [p for p in produtos if codigo_q in str(p.get("codigo") or "").strip().lower()]
    if codigobarra_q:
        produtos = [p for p in produtos if codigobarra_q in str(p.get("codigobarra") or "").strip().lower()]

    # ------ IMAGENS: monta imagem URL a partir da pasta ------
    extensoes = [".jpg", ".jpeg", ".png", ".webp", ".JPG", ".JPEG", ".PNG", ".WEBP"]

    cnpj_limpo = limpa_cnpj(cnpj) if cnpj else ""
    pasta_cnpj = os.path.join(UPLOAD_DIR, cnpj_limpo) if cnpj_limpo else None

    for p in produtos:
        chosen = None
        codigo_item = str(p.get("codigo") or "").strip()

        if codigo_item and pasta_cnpj and os.path.exists(pasta_cnpj):
            arquivos = os.listdir(pasta_cnpj)
            for ext in extensoes:
                for arquivo in arquivos:
                    nome_base, arquivo_ext = os.path.splitext(arquivo)
                    if nome_base.lower() == codigo_item.lower() and arquivo_ext.lower() == ext.lower():
                        chosen = arquivo
                        break
                if chosen:
                    break

        # Se não encontrou, usa imagem padrão
        if chosen:
            p["imagem_url"] = f"/{UPLOAD_DIR}/{cnpj_limpo}/{chosen}"
        else:
            p["imagem_url"] = f"/{UPLOAD_DIR}/{cnpj_limpo}/{IMAGEM_PADRAO}"

        # ------ Formata preço ------
        try:
            prec = float(p.get("precovenda") or 0)
        except Exception:
            prec = 0.0
        p["precovenda_str"] = f"R$ {prec:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # ------ retorna template ------
    return templates.TemplateResponse(
        "produto/listar_produtos.html",
        {
            "request": request,
            "produtos": produtos,
            "empresa_nome": empresa_nome,
            "empresa_cnpj": cnpj,
            "empresa_token": token,
        }
    )

# =====================================================================================================================|
#                          UPLOAD DE IMAGEM NA LISTA DE PRODUTOS
# =====================================================================================================================|
@upload_imagem_produtos_router.post("/")
async def upload_imagem_produto(
    cnpj: str = Form(...),
    codigo: str = Form(...),
    file: UploadFile = Form(...)
):
    logging.warning(f"Exibir CNPJ: {cnpj}")

    if not cnpj or not codigo:
        return JSONResponse({"success": False, "msg": "CNPJ ou código ausente"})

    # Remove caracteres não numéricos do CNPJ
    cnpj_clean = "".join(filter(str.isdigit, cnpj))

    # Cria pasta se não existir
    pasta = os.path.join("static", "img", cnpj_clean)
    os.makedirs(pasta, exist_ok=True)

    # Caminho completo do arquivo
    caminho = os.path.join(pasta, f"{codigo}.jpg")

    try:
        # Salva o arquivo
        with open(caminho, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"success": True}
    except Exception as e:
        logging.error(f"Erro ao salvar imagem: {e}")
        return JSONResponse({"success": False, "msg": "Erro ao salvar imagem"})