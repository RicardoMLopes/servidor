import asyncio
from datetime import datetime
from sqlalchemy.exc import OperationalError
import pymysql.err
from dependencies import get_controle_session, get_empresa_session, todos_nome_banco
from querys import ConsultaEmpresa, ConsultaProduto, ConsultaParametroporempresa, AtualizarParametro
from routes.gerar_catalogo import gerar_catalogo_pdf

async def gerar_catalogo_diario():
    agora = datetime.now()
    controle_db = get_controle_session()

    try:
        empresas = todos_nome_banco()  # lista de dicts: db_name, cnpj, nome
        if not empresas:
            print("⚠️ Nenhuma empresa encontrada no banco de controle")
            return

        for empresa in empresas:
            db_name = empresa.get("db_name")
            cnpj = empresa.get("cnpj")
            nome_empresa = empresa.get("nome")
            print(f"\n🔹 Verificando catálogo para {nome_empresa} ({cnpj})")

            empresa_db = None
            try:
                # Conecta no banco da empresa
                try:
                    empresa_db = get_empresa_session(db_name)
                    print(f"🔗 Conectando no banco: {empresa_db.bind.url}")
                except (OperationalError, pymysql.err.InternalError) as db_err:
                    print(f"❌ Banco da empresa '{nome_empresa}' ({db_name}) não encontrado: {db_err}")
                    continue

                # Consulta último parâmetro do catálogo
                parametro = ConsultaParametroporempresa(empresa_db)
                ultima = parametro["datacatalogo"] if parametro else None

                if ultima:
                    # Compara apenas a data (ignorando hora/minuto)
                    if ultima.date() == agora.date():
                        print(f"📌 Catálogo já gerado hoje para {nome_empresa}")
                        continue

                # Consulta dados da empresa
                dados_empresa = ConsultaEmpresa(empresa_db)
                if not dados_empresa:
                    print(f"⚠️ Empresa {nome_empresa} não encontrada na base {db_name}")
                    continue

                # Consulta produtos
                produtos = ConsultaProduto(empresa_db)

                if not produtos:
                    print(f"⚠️ Nenhum produto encontrado para {nome_empresa}")
                    continue

                # Gera PDF
                print(f"🖨️ Gerando catálogo para {nome_empresa}")
                await gerar_catalogo_pdf(produtos, empresa_db)

                # Atualiza parâmetro datacatalogo com data e hora atuais
                AtualizarParametro(empresa_db, "datacatalogo", agora)
                print(f"✅ Catálogo gerado e parâmetro atualizado para {nome_empresa}")

            except Exception as e:
                print(f"❌ Erro ao gerar catálogo para {nome_empresa}: {e}")

            finally:
                if empresa_db:
                    empresa_db.close()

    except Exception as e:
        print(f"❌ Erro no processo de geração diária do catálogo: {e}")

    finally:
        controle_db.close()
