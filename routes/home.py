import os, re
import shutil
from typing import List
from fastapi import FastAPI, Request, Form, UploadFile, File, Cookie, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from database.connection import DB_CHAVE, get_empresa_session
from database.querys import ConsultaEmpresaPorCNPJ, Consultar_vendedor_user
from function.funtions import templates, processar_imagem, gerar_token_cnpj, limpa_cnpj
from params.logger_config import logger
from routes.sicronizeimage import get_nome_banco_por_token
from sqlalchemy.orm import Session
from database.querys import ConsultaUsuarioPorUsername
from function.funtions import hash_password, verificar_senha

home_router = APIRouter()


@home_router.get("/", response_class=HTMLResponse)
async def home(request: Request, msg: str = None):
    return templates.TemplateResponse("home.html", {"request": request, "msg": msg})



@home_router.post("/identificar-empresa/")
async def identificar_empresa(request: Request, cnpj: str = Form(...)):

    print("identificar empresa", cnpj)
    # Limpa o CNPJ/CPF
    cnpj = re.sub(r"\D", "", cnpj)

    # Validação básica CPF (11) ou CNPJ (14)
    if len(cnpj) not in (11, 14):
        return JSONResponse({"success": False, "msg": "CPF ou CNPJ inválido!"})

    try:
        # Gerar token
        token = gerar_token_cnpj(cnpj, DB_CHAVE)

        # Descobrir nome do banco pelo token (e grava o token no banco se ainda não existir)
        nome_banco = get_nome_banco_por_token(token, cnpj)
        if not nome_banco:
            return JSONResponse(
                {"success": False, "msg": "Empresa não encontrada."}
            )

        # Cria sessão da empresa e consulta dados
        session_empresa = get_empresa_session(nome_banco)
        with session_empresa as db:
            print(f"[LOG] Executando ConsultaEmpresaPorCNPJ no banco '{nome_banco}' para o CNPJ/CPF '{cnpj}'")
            empresa_raw = ConsultaEmpresaPorCNPJ(db, cnpj)
            print(f"[LOG] Resultado da ConsultaEmpresaPorCNPJ: {empresa_raw}")

            if not empresa_raw:
                return JSONResponse(
                    {"success": False, "msg": "Empresa não encontrada."}
                )

            empresa = empresa_raw[0]

        # Retorna JSON com sucesso, dados da empresa e token
        return JSONResponse({
            "success": True,
            "empresa": {
                "codigo": empresa["codigo"],
                "nome": empresa["nome"],
                "cnpj": empresa["cnpj"],
            },
            "token": token,
        })

    except Exception as e:
        print("Erro ao consultar empresa:", e)
        return JSONResponse({ "success": False, "msg": "Erro ao consultar empresa. Tente novamente.", })


@home_router.get("/dashboard/")
async def dashboard(request: Request):
    # 1. Recupera cookies da empresa
    empresa_cnpj = request.cookies.get("empresa_cnpj")
    empresa_token = request.cookies.get("empresa_token")

    # 2. Recupera cookies do usuário logado (Novo)
    usuario_id = request.cookies.get("usuario_id")
    usuario_nome = request.cookies.get("usuario_nome")

    if not empresa_cnpj or not empresa_token:
        return RedirectResponse("/", status_code=303)

    # Se a empresa já foi identificada, mas o usuário AINDA NÃO logou -> Vai para a tela de Login/Cadastro
    if not usuario_id:
        return RedirectResponse("/login-usuario", status_code=303)

    try:
        nome_banco = get_nome_banco_por_token(empresa_token)
        if not nome_banco:
            return RedirectResponse("/", status_code=303)

        session_empresa = get_empresa_session(nome_banco)
        with session_empresa as db:
            empresa_raw = ConsultaEmpresaPorCNPJ(db, empresa_cnpj)
            if not empresa_raw:
                return RedirectResponse("/", status_code=303)

            empresa = empresa_raw[0]

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "empresa_cnpj": empresa["cnpj"],
                "empresa_token": empresa_token,
                "empresa_nome": empresa["nome"],
                "usuario_id": usuario_id,
                "usuario_nome": usuario_nome,
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


@home_router.get("/api/obter-token-cnpj/{cnpj}")
async def obter_token_por_cnpj(cnpj: str):
    try:
        # Usa a mesma função que você já tem no projeto
        token = gerar_token_cnpj(cnpj, DB_CHAVE)

        if not token:
            raise HTTPException(status_code=404, detail="Token não encontrado para este CNPJ.")

        return JSONResponse(content={"sucesso": True, "token": token})

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar token para o CNPJ {cnpj}: {str(e)}"
        )


from fastapi import Request, status
from fastapi.responses import RedirectResponse


@home_router.post("/logout")
async def logout(request: Request):
    # Redireciona para a tela inicial (ou para /login-usuario se quiser manter a empresa selecionada)
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    # 1. Cookies da Empresa (Identificação do Tenant/Banco)
    response.delete_cookie(key="empresa_cnpj", path="/")
    response.delete_cookie(key="empresa_token", path="/")
    response.delete_cookie(key="cnpj", path="/")

    # 2. Cookies do Usuário Logado (Novos)
    response.delete_cookie(key="usuario_id", path="/")
    response.delete_cookie(key="usuario_nome", path="/")
    response.delete_cookie(key="vendedor_codigo", path="/")
    response.delete_cookie(key="empresa_codigo", path="/")

    # 3. Cookies Legados/Sessão Geral
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="session", path="/")

    # 4. Controle de Cache (Evita navegação pelo botão "Voltar" do browser)
    response.headers["Cache-Control"] = (
        "no-cache, no-store, must-revalidate, private, max-age=0"
    )
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response

@home_router.get("/login-usuario", response_class=HTMLResponse)
async def tela_login_usuario(request: Request):
    empresa_cnpj = request.cookies.get("empresa_cnpj")
    empresa_token = request.cookies.get("empresa_token")

    # Se não houver cookies da empresa, volta para a tela inicial de CNPJ
    if not empresa_cnpj or not empresa_token:
        return RedirectResponse("/", status_code=303)

    try:
        nome_banco = get_nome_banco_por_token(empresa_token)
        if not nome_banco:
            return RedirectResponse("/", status_code=303)

        session_empresa = get_empresa_session(nome_banco)
        with session_empresa as db:
            empresa_raw = ConsultaEmpresaPorCNPJ(db, empresa_cnpj)
            if not empresa_raw:
                return RedirectResponse("/", status_code=303)

            empresa = empresa_raw[0]

        return templates.TemplateResponse("login/login_user.html", {
            "request": request,
            "empresa_nome": empresa["nome"],
            "empresa_cnpj": empresa["cnpj"],
            "error": None
        })

    except Exception as e:
        print("Erro ao carregar tela de login do usuário:", e)
        return RedirectResponse("/", status_code=303)



@home_router.post("/autenticar-usuario")
async def autenticar_usuario(
    request: Request,
    usuario: str = Form(...),
    senha: str = Form(...)
):
    empresa_token = request.cookies.get("empresa_token")
    empresa_cnpj = request.cookies.get("empresa_cnpj")

    if not empresa_token or not empresa_cnpj:
        return RedirectResponse("/", status_code=303)

    try:
        nome_banco = get_nome_banco_por_token(empresa_token)
        if not nome_banco:
            return RedirectResponse("/", status_code=303)

        session_empresa = get_empresa_session(nome_banco)

        with session_empresa as db:
            empresa_raw = ConsultaEmpresaPorCNPJ(db, empresa_cnpj)
            empresa_nome = empresa_raw[0]["nome"] if empresa_raw else ""

            # Busca o usuário na tabela cadusers
            senha_hash = hash_password(senha)
            usuario_raw = ConsultaUsuarioPorUsername(db, usuario)

            if not usuario_raw:
                return templates.TemplateResponse(
                    "login/login_user.html",
                    {
                        "request": request,
                        "empresa_nome": empresa_nome,
                        "empresa_cnpj": empresa_cnpj,
                        "error": "Usuário ou senha incorretos."
                    },
                    status_code=400
                )

            user = usuario_raw[0]
            hash_digitado = hash_password(senha)

            senha_valida = verificar_senha(senha, user["senha"])

            print("========================================")
            print("USUÁRIO:", user["usuario"])
            print("SENHA DIGITADA:", repr(senha))
            print("HASH GERADO:", hash_password(senha))
            print("HASH BANCO:", repr(user["senha"]))
            print("HASHES IGUAIS:", hash_password(senha) == user["senha"])
            print("SENHA VÁLIDA:", senha_valida)
            print("TIPO SENHA VÁLIDA:", type(senha_valida))
            print("========================================")

            # Valida a senha
            if not verificar_senha(senha, user["senha"]):
                return templates.TemplateResponse(
                    "login/login_user.html",
                    {
                        "request": request,
                        "empresa_nome": empresa_nome,
                        "empresa_cnpj": empresa_cnpj,
                        "error": "Usuário ou senha incorretos."
                    },
                    status_code=400
                )

            # Usuário autenticado
            response = RedirectResponse(
                url="/dashboard/",
                status_code=303
            )

            response.set_cookie(
                key="usuario_id",
                value=str(user["id"]),
                httponly=True
            )

            response.set_cookie(
                key="usuario_nome",
                value=str(user["usuario"]),
                httponly=True
            )

            response.set_cookie(
                key="empresa_codigo",
                value=str(user["empresa"]),
                httponly=True
            )

            response.set_cookie(
                key="vendedor_codigo",
                value=str(user["codigovendedor"] or ""),
                httponly=True
            )

            return response

    except Exception as e:
        print("Erro durante a autenticação do usuário:", e)

        return templates.TemplateResponse(
            "login/login_user.html",
            {
                "request": request,
                "empresa_nome": "",
                "empresa_cnpj": empresa_cnpj,
                "error": "Ocorreu um erro interno ao autenticar. Tente novamente."
            },
            status_code=500
        )