from datetime import datetime, timedelta
from database.dependencies import get_controle_session, get_empresa_session, todos_nome_banco
from database.querys import ConsultaEmpresa, ConsultaProduto, ConsultaParametroporempresa, AtualizarParametro
from routes.gerar_catalogo import gerar_catalogo_pdf
import os
from params.alerta import enviar_alerta


LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def log_msg(msg: str):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = f"[{agora}] {msg}"
    print(linha)
    # Salva em arquivo diário
    with open(os.path.join(LOG_DIR, f"log_{datetime.now().date()}.txt"), "a", encoding="utf-8") as f:
        f.write(linha + "\n")

async def gerar_catalogo_diario():
    agora = datetime.now()
    controle_db = get_controle_session()

    try:
        empresas = todos_nome_banco()
        if not empresas:
            log_msg("⚠️ Nenhuma empresa encontrada no banco de controle")
            return

        for empresa in empresas:
            db_name = empresa.get("db_name")
            nome_empresa = empresa.get("nome")
            log_msg(f"\n🔹 Verificando catálogo para {nome_empresa}")

            empresa_db = None
            try:
                empresa_db = get_empresa_session(db_name)

                parametro = ConsultaParametroporempresa(empresa_db)
                ultima = parametro["datacatalogo"] if parametro else None

                if ultima and (agora - ultima < timedelta(hours=1)):
                    log_msg(f"⏱️ Ainda não passou 1 hora desde a última geração para {nome_empresa}")
                    continue

                dados_empresa = ConsultaEmpresa(empresa_db)
                produtos = ConsultaProduto(empresa_db)

                if not dados_empresa or not produtos:
                    log_msg(f"⚠️ Dados insuficientes para {nome_empresa}")
                    continue

                log_msg(f"🖨️ Gerando catálogo para {nome_empresa}")
                await gerar_catalogo_pdf(produtos, empresa_db)

                AtualizarParametro(empresa_db, "datacatalogo", agora)
                log_msg(f"✅ Catálogo gerado e parâmetro atualizado para {nome_empresa}")


            except Exception as e:
                msg_erro = f"❌ Erro ao gerar catálogo para {nome_empresa}: {e}"
                log_msg(msg_erro)
                # Envia alerta por email
                enviar_alerta(assunto=f"Falha ao gerar catálogo: {nome_empresa}", mensagem=msg_erro )

            finally:
                if empresa_db:
                    empresa_db.close()

    finally:
        controle_db.close()
