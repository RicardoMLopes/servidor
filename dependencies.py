from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from connection import get_controle_session, get_empresa_session
from sqlalchemy import text


# Extrai token do header
def get_token(request: Request) -> str:
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Token não fornecido")
    return token.replace("Bearer ", "").strip()

# Pega o nome do banco da empresa com base no token
def get_nome_banco_por_token(token: str) -> str:
    session = get_controle_session()
    with session as db:
        result = db.execute( text(
            "SELECT banco FROM controle WHERE token = :token"),
            {"token": token}
        ).fetchone()
        if not result:
            raise HTTPException(status_code=403, detail="Token inválido ou empresa não encontrada")
        return result[0]

# Dependência principal usada nas rotas
def get_empresa_db(request: Request) -> Session:
    token = get_token(request)
    nome_banco = get_nome_banco_por_token(token)
    return get_empresa_session(nome_banco)

# Dependência principal usada nas rotas web
def get_empresa_db_por_token(token: str):
    nome_banco = get_nome_banco_por_token(token)
    return get_empresa_session(nome_banco)
