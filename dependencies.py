import traceback
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
    try:
        session = get_controle_session()
        with session as db:
            result = db.execute( text(
                "SELECT banco FROM controle WHERE token = :token"),
                {"token": token}
            ).fetchone()
            if not result:
                raise HTTPException(status_code=403, detail="Token inválido ou empresa não encontrada")
            return result[0]
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        return None

    finally:
        db.close()


# Dependência principal usada nas rotas
def get_empresa_db(request: Request) -> Session:
    token = get_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Token não fornecido")

    try:
        nome_banco = get_nome_banco_por_token(token)
        if not nome_banco:
            raise HTTPException(status_code=404, detail="Token inválido ou banco não encontrado")

        return get_empresa_session(nome_banco)

    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao obter sessão do banco: {e.__class__.__name__}: {str(e)}")

# Dependência principal usada nas rotas web
def get_empresa_db_por_token(token: str):
    nome_banco = get_nome_banco_por_token(token)
    return get_empresa_session(nome_banco)
