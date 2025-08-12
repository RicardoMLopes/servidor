from fastapi import Request, Header, HTTPException, APIRouter
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
import os
from dependencies import get_controle_session, get_empresa_session  # ajuste os imports


imagem_router = APIRouter()

# Obtém o token do header
def get_token(request: Request) -> str:
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Token não fornecido")
    return token.replace("Bearer ", "").strip()

# Busca o nome do banco da empresa pelo token
def get_nome_banco_por_token(token: str) -> str:
    session = get_controle_session()
    with session as db:
        result = db.execute(
            text("SELECT banco FROM controle WHERE token = :token"),
            {"token": token}
        ).fetchone()
        if not result:
            raise HTTPException(status_code=403, detail="Token inválido ou empresa não encontrada")
        return result[0]

# Busca o CNPJ da empresa no banco da empresa
def get_cnpj_por_banco(nome_banco: str) -> str:
    session = get_empresa_session(nome_banco)
    with session as db:
        result = db.execute(text("SELECT cnpj FROM cadempresa LIMIT 1")).fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="CNPJ da empresa não encontrado")
        return result[0].replace("/", "").replace(".", "").replace("-", "").strip()

# Rota de imagens
@imagem_router.get("/imagem")
def sincroniza_imagens(request: Request):
    token = get_token(request)
    nome_banco = get_nome_banco_por_token(token)
    cnpj = get_cnpj_por_banco(nome_banco)
    print("CNPJ resolvido:", cnpj)

    pasta = os.path.join("static", "img", cnpj)
    print("Caminho da pasta:", pasta)
    if not os.path.exists(pasta):
        return {"imagens": []}

    arquivos = os.listdir(pasta)
    base_url = str(request.base_url)

    imagens = [
        base_url + f"static/img/{cnpj}/{arquivo}"
        for arquivo in arquivos
        if arquivo.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    ]

    return {"imagens": imagens}
