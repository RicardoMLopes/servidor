from fastapi import Request, HTTPException, APIRouter, BackgroundTasks
from sqlalchemy.sql import text
import os
import asyncio
from database.dependencies import get_controle_session, get_empresa_session
from .gerar_catalogo import gerar_catalogo_pdf

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
def sincroniza_imagens(request: Request, background_tasks: BackgroundTasks):
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

        # =========================
        # GERAR CATÁLOGO (BACKGROUND)
        # =========================
        caminho_pdf = os.path.join(pasta, "catalogo.pdf")

        if not os.path.exists(caminho_pdf):
            print("📄 Catálogo não existe → será gerado em background")

            try:
                session_empresa = get_empresa_session(nome_banco)

                def task_gerar_catalogo():
                    try:
                        with session_empresa as db:
                            dados = db.execute(
                                text("SELECT * FROM cadproduto ORDER BY TRIM(descricao) ASC")
                            ).fetchall()

                            # 🔥 AQUI NÃO USA asyncio.run
                            import asyncio
                            asyncio.run(gerar_catalogo_pdf(dados, db))

                        print("✅ Catálogo gerado com sucesso (background)")

                    except Exception as e:
                        print(f"❌ Erro ao gerar catálogo (background): {e}")

                background_tasks.add_task(task_gerar_catalogo)

            except Exception as e:
                print(f"❌ Erro ao preparar geração do catálogo: {e}")

        # =========================
        # LISTAR ARQUIVOS
        # =========================
        base_url = str(request.base_url)
        imagens_para_baixar = []

        try:
            for arquivo in os.scandir(pasta):

                if not arquivo.is_file():
                    continue

                ext = os.path.splitext(arquivo.name)[1].lower()

                if ext in [".pdf", ".jpg", ".jpeg", ".png", ".webp"]:

                    mtime = int(os.path.getmtime(arquivo.path))

                    imagens_para_baixar.append({
                        "url": base_url + f"static/img/{cnpj}/{arquivo.name}",
                        "mtime": mtime
                    })

        except Exception as e:
            print(f"❌ Erro ao listar arquivos: {e}")

        # =========================
        # GARANTIR SEM_IMAGEM
        # =========================
        caminho_sem_imagem = os.path.join(pasta, "sem_imagem.jpg")

        if os.path.exists(caminho_sem_imagem):
            imagens_para_baixar.append({
                "url": base_url + f"static/img/{cnpj}/sem_imagem.jpg",
                "mtime": int(os.path.getmtime(caminho_sem_imagem))
            })

        print(f"[INFO] Total de arquivos para sincronizar: {len(imagens_para_baixar)}")

        return {"imagens": imagens_para_baixar}

    except Exception as e:
        print(f"[ERRO] Exceção ao sincronizar imagens: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao sincronizar imagens")
