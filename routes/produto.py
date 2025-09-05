import ast
import os
from datetime import datetime
from typing import Optional
import pytz
from fastapi import APIRouter
from fastapi import Query, Request
from starlette.responses import HTMLResponse
from typing import List
from database.connection import get_empresa_session, DB_CHAVE
from function.funtions import gerar_token_cnpj, limpa_cnpj
from params.alerta import enviar_alerta
from database.querys import ConsultaProduto, Insert_Produto, ConsultaEmpresa
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from database.dependencies import get_empresa_db, get_nome_banco_por_token
import traceback

from routes.pedidovenda import templates

products_router = APIRouter()
list_products_router = APIRouter()

@products_router.get("")
async def listar_produtos(
    last_sync: Optional[str] = Query(
        None,
        description="Data/hora da última sincronização (ISO 8601)"
    ),
    db: Session = Depends(get_empresa_db)
):
   # logging.warning("Exibir data: %s", last_sync)
    try:
        filtro_data: Optional[datetime] = None
        if last_sync:
            try:
                filtro_data = datetime.fromisoformat(last_sync)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Formato inválido de last_sync. Use ISO 8601 (ex: 2025-08-27T10:15:00)"
                )

        # Consulta produtos no banco, filtrando por data se last_sync informado
        resultado = ConsultaProduto(db, filtro_data)

        # Define as colunas do retorno
        colunas = [
            "empresa", "codigo", "descricao", "unidadeMedida", "codigobarra",
            "agrupamento", "marca", "modelo", "tamanho", "cor", "peso",
            "precovenda", "casasdecimais", "percentualdesconto", "estoque",
            "reajustacondicaopagamento", "percentualComissao", "situacaoregistro",
            "dataRegistro", "versao", "imagens"
        ]

        dados = []
        for item in resultado:
            if len(item) != len(colunas):
                dados.append({col: item[i] if i < len(item) else None for i, col in enumerate(colunas)})
            else:
                dados.append(dict(zip(colunas, item)))

        # Usa pytz para pegar hora de São Paulo
        tz_sp = pytz.timezone("America/Sao_Paulo")
        last_sync_servidor = datetime.now(tz_sp)

        return {
            "produtos": dados,
            "last_sync": last_sync_servidor
        }

    except HTTPException as e:
        raise e
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
):
    # ------ autenticação / token (igual ao seu fluxo) ------
    if not token and cnpj:
        token = gerar_token_cnpj(cnpj, DB_CHAVE)

    if not token:
        # retorna template vazio — formulario precisa reenviar token/cnpj
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

    # ------ pega produtos (sua consulta existente) ------
    resultado = ConsultaProduto(db)
    colunas = [
        "empresa","codigo","descricao","unidadeMedida","codigobarra",
        "agrupamento","marca","modelo","tamanho","cor","peso",
        "precovenda","casasdecimais","percentualdesconto","estoque",
        "reajustacondicaopagamento","percentualComissao","situacaoregistro",
        "dataRegistro","versao","imagens"
    ]

    produtos = []
    for item in resultado:
        # se item já for dict, use direto; senão zippa com colunas
        if isinstance(item, dict):
            p = item.copy()
        else:
            # cuidado com comprimentos diferentes
            if len(item) != len(colunas):
                p = {col: item[i] if i < len(item) else None for i, col in enumerate(colunas)}
            else:
                p = dict(zip(colunas, item))
        produtos.append(p)

    # ------ NORMALIZAÇÕES úteis ------
    # normaliza a lista de imagens (p["imagens"]) para uma lista de nomes de arquivo
    def normalize_imagens_field(imagens_field) -> List[str]:
        if not imagens_field:
            return []
        # se já é lista/tuple
        if isinstance(imagens_field, (list, tuple)):
            return [str(x).strip() for x in imagens_field if str(x).strip()]
        # se for bytes
        if isinstance(imagens_field, bytes):
            imagens_field = imagens_field.decode('utf-8', errors='ignore')
        # se for string: pode ser "['a.jpg']" (JSON/python list) ou "a.jpg,b.jpg"
        if isinstance(imagens_field, str):
            s = imagens_field.strip()
            # tenta interpretar como literal Python (ex: "['a.jpg','b.png']")
            try:
                parsed = ast.literal_eval(s)
                if isinstance(parsed, (list, tuple)):
                    return [str(x).strip() for x in parsed if str(x).strip()]
            except Exception:
                pass
            # fallback: split por vírgula
            parts = [p.strip() for p in s.split(',') if p.strip()]
            return parts
        return []

    # ------ APLICA FILTROS em Python (robustos) ------
    descricao_q = descricao.strip().lower() if descricao and descricao.strip() else None
    agrupamento_q = agrupamento.strip().lower() if agrupamento and agrupamento.strip() else None

    if descricao_q:
        produtos = [p for p in produtos if descricao_q in str(p.get("descricao") or "").strip().lower()]

    if agrupamento_q:
        produtos = [p for p in produtos if agrupamento_q in str(p.get("agrupamento") or "").strip().lower()]

    # ------ IMAGENS: monta imagem URL preferindo arquivos reais na pasta ------
    cnpj_limpo = limpa_cnpj(cnpj) if cnpj else ""
    pasta_cnpj = os.path.join(UPLOAD_DIR, cnpj_limpo) if cnpj_limpo else None

    for p in produtos:
        # normaliza imagens field
        imagens_field = p.get("imagens")
        imgs = normalize_imagens_field(imagens_field)

        chosen = None

        # 1) se o campo imagens contém nomes, prefira o primeiro que exista na pasta
        if imgs and pasta_cnpj and os.path.exists(pasta_cnpj):
            for nome_img in imgs:
                caminho = os.path.join(pasta_cnpj, nome_img)
                if os.path.exists(caminho):
                    chosen = nome_img
                    break

        # 2) se não encontrou, tente pelo padrão codigo + extensões conhecidas
        if not chosen:
            codigo = str(p.get("codigo") or "").strip()
            if codigo and pasta_cnpj and os.path.exists(pasta_cnpj):
                for ext in [".jpg", ".jpeg", ".png", ".webp"]:
                    nome_img = f"{codigo}{ext}"
                    caminho = os.path.join(pasta_cnpj, nome_img)
                    if os.path.exists(caminho):
                        chosen = nome_img
                        break

        # 3) monta URL final
        if chosen:
            p["imagem_url"] = f"/{UPLOAD_DIR}/{cnpj_limpo}/{chosen}"
        else:
            # tenta imagem padrão na pasta do cnpj; se não existir, usa global
            pad_local = os.path.join(UPLOAD_DIR, cnpj_limpo, IMAGEM_PADRAO) if cnpj_limpo else None
            if pad_local and os.path.exists(pad_local):
                p["imagem_url"] = f"/{UPLOAD_DIR}/{cnpj_limpo}/{IMAGEM_PADRAO}"
            else:
                # fallback global
                p["imagem_url"] = f"/{UPLOAD_DIR}/{IMAGEM_PADRAO}"

        # formata preço (garante float safe)
        try:
            prec = float(p.get("precovenda") or 0)
        except Exception:
            prec = 0.0
        p["precovenda_str"] = f"R$ {prec:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # ------ retorna template (PASSAR token/cnpj para o FORM) ------
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
