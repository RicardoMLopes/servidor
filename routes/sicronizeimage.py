from fastapi import Request, HTTPException, APIRouter, BackgroundTasks
from sqlalchemy.sql import text
import os, re
import asyncio
from database.dependencies import get_controle_session, get_empresa_session
from .gerar_catalogo import gerar_catalogo_pdf

imagem_router = APIRouter()

def get_token(request: Request) -> str:
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Token não fornecido")
    return token.replace("Bearer ", "").strip()

def get_nome_banco_por_token(token: str, cnpj: str = None) -> str:
    print(f"\n[LOG - INICIO] get_nome_banco_por_token")
    print(f"[LOG] Token recebido: {token}")
    print(f"[LOG] CNPJ recebido: {cnpj}")

    session = get_controle_session()
    with session as db:
        # 1. Tenta buscar direto pelo token
        print("[LOG - Passo 1] Consultando banco pelo TOKEN...")
        result = db.execute(
            text("SELECT banco FROM controle WHERE token = :token"),
            {"token": token},
        ).fetchone()

        if result:
            print(
                f"[LOG - Passo 1 SUCCESSO] Empresa encontrada pelo token! Banco:"
                f" {result[0]}"
            )
            return result[0]

        print(
            "[LOG - Passo 1 FALHA] Nenhum registro encontrado para este token."
        )

        # 2. Se não achou pelo token mas veio o CNPJ, busca pelo CNPJ e grava o token
        if cnpj:
            cnpj_limpo = re.sub(r"\D", "", cnpj)
            print(
                f"[LOG - Passo 2] Buscando pelo CNPJ limpo no banco:"
                f" '{cnpj_limpo}'..."
            )

            result_cnpj = db.execute(
                text("""
                    SELECT banco, codigo 
                    FROM controle 
                    WHERE REPLACE(REPLACE(REPLACE(codigo, '.', ''), '/', ''), '-', '') = :cnpj
                """),
                {"cnpj": cnpj_limpo},
            ).fetchone()

            if result_cnpj:
                nome_banco, codigo_empresa = result_cnpj[0], result_cnpj[1]
                print(
                    f"[LOG - Passo 2 SUCESSO] Registro encontrado por CNPJ! Código:"
                    f" {codigo_empresa} | Banco: {nome_banco}"
                )

                # Grava o token gerado para as próximas consultas
                print(
                    f"[LOG - Passo 2] Atualizando tabela 'controle' com o novo"
                    f" token para a empresa {codigo_empresa}..."
                )
                db.execute(
                    text(
                        "UPDATE controle SET token = :token WHERE codigo ="
                        " :codigo"
                    ),
                    {"token": token, "codigo": codigo_empresa},
                )
                db.commit()
                print(
                    "[LOG - Passo 2] Token gravado e commit realizado com"
                    " sucesso!"
                )

                return nome_banco.strip()
            else:
                print(
                    f"[LOG - Passo 2 FALHA] CNPJ '{cnpj_limpo}' não encontrado"
                    " na coluna 'codigo' da tabela 'controle'."
                )
        else:
            print(
                "[LOG - Passo 2 ALERTA] Parâmetro CNPJ é None. Impossível"
                " recuperar por CNPJ."
            )

        print("[LOG - ERRO FINAL] Lançando HTTPException 403\n")
        raise HTTPException(
            status_code=403,
            detail="Token inválido ou empresa não encontrada",
        )

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
