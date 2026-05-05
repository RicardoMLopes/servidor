import os, re
import shutil
from typing import List
from fastapi import FastAPI, Request, Form, UploadFile, File, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from database.connection import DB_CHAVE, get_empresa_session
from database.querys import ConsultaEmpresaPorCNPJ, Consultar_vendedor_user
from function.funtions import templates, processar_imagem, gerar_token_cnpj, limpa_cnpj
from params.logger_config import logger
from routes.sicronizeimage import get_nome_banco_por_token

home_router = APIRouter()


@home_router.get("/", response_class=HTMLResponse)
async def home(request: Request, msg: str = None):
    return templates.TemplateResponse("home.html", {"request": request, "msg": msg})



@home_router.post("/identificar-empresa/")
async def identificar_empresa(request: Request, cnpj: str = Form(...)):
    # Limpa o CNPJ/CPF
    cnpj = re.sub(r"\D", "", cnpj)

    # Validação básica CPF (11) ou CNPJ (14)
    if len(cnpj) not in (11, 14):
        return JSONResponse({"success": False, "msg": "CPF ou CNPJ inválido!"})

    try:
        # Gerar token
        token = gerar_token_cnpj(cnpj, DB_CHAVE)

        # Descobrir nome do banco pelo token
        nome_banco = get_nome_banco_por_token(token)
        if not nome_banco:
            return JSONResponse({"success": False, "msg": "Empresa não encontrada."})

        # Cria sessão da empresa e consulta dados
        session_empresa = get_empresa_session(nome_banco)
        with session_empresa as db:
            empresa_raw = ConsultaEmpresaPorCNPJ(db, cnpj)
            if not empresa_raw:
                return JSONResponse({"success": False, "msg": "Empresa não encontrada."})

            empresa = empresa_raw[0]  # Pega o primeiro registro

        # Retorna JSON com sucesso, dados da empresa e token
        return JSONResponse({
            "success": True,
            "empresa": {
                "codigo": empresa["codigo"],
                "nome": empresa["nome"],
                "cnpj": empresa["cnpj"]
            },
            "token": token
        })

    except Exception as e:
        print("Erro ao consultar empresa:", e)
        return JSONResponse({"success": False, "msg": "Erro ao consultar empresa. Tente novamente."})


@home_router.get("/dashboard/")
async def dashboard(request: Request):
    # Pega os cookies definidos pelo JS
    empresa_cnpj = request.cookies.get("empresa_cnpj")
    empresa_token = request.cookies.get("empresa_token")

    if not empresa_cnpj or not empresa_token:
        # Se não houver cookies, volta para a home
        return RedirectResponse("/", status_code=303)

    try:
        # Descobre o nome do banco pelo token
        nome_banco = get_nome_banco_por_token(empresa_token)
        if not nome_banco:
            return RedirectResponse("/", status_code=303)

        # Cria sessão da empresa e busca os dados
        session_empresa = get_empresa_session(nome_banco)
        with session_empresa as db:
            empresa_raw = ConsultaEmpresaPorCNPJ(db, empresa_cnpj)
            if not empresa_raw:
                return RedirectResponse("/", status_code=303)

            empresa = empresa_raw[0]  # Pega o primeiro registro

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "empresa_cnpj": empresa["cnpj"],
                "empresa_token": empresa_token,
                "empresa_nome": empresa["nome"]
            }
        )

    except Exception as e:
        print("Erro ao carregar dashboard:", e)
        return RedirectResponse("/", status_code=303)



UPLOAD_DIR = "static/img"

@home_router.post("/upload")
async def upload_image(
    cnpj: str = Form(...),
    files: List[UploadFile] = File(...)
):
    try:
        cnpj = limpa_cnpj(cnpj.strip())
        print(f"📌 CNPJ: {cnpj}")

        pasta_empresa = os.path.join(UPLOAD_DIR, cnpj)
        os.makedirs(pasta_empresa, exist_ok=True)

        arquivos_processados = []

        for file in files:
            try:
                # 🔹 Nome seguro
                nome_original = file.filename.replace(" ", "_").lower()

                # 🔹 Caminho temporário
                temp_path = os.path.join(pasta_empresa, nome_original)

                with open(temp_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

                # 🔹 Nome final padronizado (.jpg)
                nome_base = os.path.splitext(nome_original)[0]
                nome_final = f"{nome_base}.jpg"
                destino = os.path.join(pasta_empresa, nome_final)

                print(f"🖼️ Processando: {temp_path} → {destino}")

                # 🔹 Processar imagem
                processar_imagem(
                    temp_path,
                    destino,
                    largura=800,
                    altura=800,
                    qualidade=85
                )

                # 🔹 Remove original se diferente
                if temp_path != destino and os.path.exists(temp_path):
                    os.remove(temp_path)

                arquivos_processados.append(nome_final)

            except Exception as e:
                print(f"Erro ao processar {file.filename}: {e}")

        return {
            "success": True,
            "msg": f"{len(arquivos_processados)} imagem(ns) processada(s) com sucesso!",
            "arquivos": arquivos_processados
        }

    except Exception as e:
        print(f"Erro geral no upload: {e}")
        return {
            "success": False,
            "msg": "Erro ao processar upload"
        }


@home_router.post("/home")
async def alterar_senha(
    senha_atual: str = Form(...), nova_senha: str = Form(...), confirmar: str = Form(...)
):
    if nova_senha != confirmar:
        return {"msg": "As senhas não coincidem!"}
    # aqui você faria a lógica de atualizar a senha no banco
    return {"msg": "Senha alterada com sucesso!"}


@home_router.post("/cadastrar-usuario")
async def cadastrar_usuario(
    nome: str = Form(...), email: str = Form(...), senha: str = Form(...)
):
    # lógica de cadastro no banco
    return {"msg": f"Usuário {nome} cadastrado com sucesso!"}


@home_router.get("/relatorios")
async def relatorios():
    # aqui pode gerar PDF, Excel ou dashboard de vendas
    return {"msg": "Relatórios de vendas em construção..."}


# GET: mostra o formulário
@home_router.get("/cadastrar-users", response_class=HTMLResponse)
async def mostrar_formulario_usuario(request: Request, cnpj: str):
    token = gerar_token_cnpj(cnpj, DB_CHAVE)
    nome_banco = get_nome_banco_por_token(token)
    session_empresa = get_empresa_session(nome_banco)

    with session_empresa as db:
        empresa_raw = ConsultaEmpresaPorCNPJ(db, cnpj)
        empresa = empresa_raw[0] if empresa_raw else None
        vendedores_raw = Consultar_vendedor_user(db)
        vendedores = [{"id": v["codigo"], "nome": v["nome"]} for v in vendedores_raw]

    return templates.TemplateResponse("cadusuario.html", {
        "request": request,
        "empresa": empresa,
        "empresa_nome": empresa.get("nome") if empresa else "",
        "vendedores": vendedores,
        "errors": {},
        "form_data": {"cnpj": cnpj}
    })