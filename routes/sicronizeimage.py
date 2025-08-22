from fastapi import Request, HTTPException, APIRouter
from sqlalchemy.sql import text
import os
from dependencies import get_controle_session, get_empresa_session

imagem_router = APIRouter()

def get_token(request: Request) -> str:
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Token não fornecido")
    return token.replace("Bearer ", "").strip()

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

def get_cnpj_por_banco(nome_banco: str) -> str:
    session = get_empresa_session(nome_banco)
    with session as db:
        result = db.execute(text("SELECT cnpj FROM cadempresa LIMIT 1")).fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="CNPJ da empresa não encontrado")
        return result[0].replace("/", "").replace(".", "").replace("-", "").strip()

@imagem_router.get("/imagem")
def sincroniza_imagens(request: Request):
    try:
        token = get_token(request)
        nome_banco = get_nome_banco_por_token(token)
        cnpj = get_cnpj_por_banco(nome_banco)
        print(f"[INFO] CNPJ resolvido: {cnpj}")

        pasta = os.path.join("static", "img", cnpj)
        print(f"[INFO] Caminho da pasta: {pasta}")
        if not os.path.exists(pasta):
            print("[AVISO] Pasta não existe")
            return {"imagens": []}

        base_url = str(request.base_url)
        arquivos = os.listdir(pasta)
        imagens_para_baixar = []

        for arquivo in arquivos:
            ext = os.path.splitext(arquivo)[1].lower()
            if ext in [".pdf", ".JPG",".jpg", ".JPEG",".jpeg", ".PNG",".png", ".webp"]:
                caminho = os.path.join(pasta, arquivo)
                mtime = os.path.getmtime(caminho)
                imagens_para_baixar.append({
                    "url": base_url + f"static/img/{cnpj}/{arquivo}",
                    "mtime": int(mtime)
                })

        # Sempre incluir sem_imagem.jpg
        caminho_sem_imagem = os.path.join(pasta, "sem_imagem.jpg")
        if os.path.exists(caminho_sem_imagem):
            mtime = os.path.getmtime(caminho_sem_imagem)
            imagens_para_baixar.append({
                "url": base_url + f"static/img/{cnpj}/sem_imagem.jpg",
                "mtime": int(mtime)
            })

        print(f"[INFO] Total de arquivos para sincronizar: {len(imagens_para_baixar)}")
        return {"imagens": imagens_para_baixar}

    except Exception as e:
        print(f"[ERRO] Exceção ao sincronizar imagens: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao sincronizar imagens")
