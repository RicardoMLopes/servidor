import logging
import os
import shutil
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import APIRouter, Depends, HTTPException
from function.funtions import templates, processar_imagem

home_router = APIRouter()


@home_router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


UPLOAD_DIR = "static/img"

@home_router.post("/upload")
async def upload_image(cnpj: str = Form(...), file: UploadFile = File(...)):
    logging.warning(f"CNPJ {cnpj}")
    pasta_empresa = os.path.join(UPLOAD_DIR, cnpj)
    os.makedirs(pasta_empresa, exist_ok=True)

    # Caminho temporário (arquivo original)
    temp_path = os.path.join(pasta_empresa, file.filename)
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Nome final sempre .jpg
    nome_final = os.path.splitext(file.filename)[0] + ".jpg"
    destino = os.path.join(pasta_empresa, nome_final)

    # Converter e salvar com padrão
    processar_imagem(temp_path, destino, largura=800, altura=800, qualidade=85)

    # Remover arquivo original se não for jpg
    if temp_path != destino and os.path.exists(temp_path):
        os.remove(temp_path)

    return {"msg": f"Imagem salva em {destino}"}


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
