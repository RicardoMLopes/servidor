import traceback, logging
from typing import Dict, Any, Optional
from params.alerta import enviar_alerta
from function.funtions import formata_cnpj, limpar_texto_mysql_auto, converter_data_mysql
from datetime import datetime
import time
from typing import List

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

logger = logging.getLogger("sincronizacao")

# OBTER A VERSÃO DO BANCO DE DADOS
# ==============================================================================
# Cache global indexado pela URL do banco do cliente
_CACHE_VERSAO_BANCO = {}

def obter_versao_major_mysql(db) -> int:
    """
    Retorna a versão do MySQL indexando o cache pelo banco de dados ativo.
    Executa 'SELECT VERSION()' apenas UMA VEZ por banco/tenant.
    """
    try:
        # Identificador único da conexão do cliente (ex: ...3306/pedidomovel)
        db_url = str(db.get_bind().url)

        if db_url not in _CACHE_VERSAO_BANCO:
            versao_raw = db.execute(text("SELECT VERSION()")).scalar()
            # Extrai o número principal (ex: '5.7.33' -> 5, '8.0.32' -> 8)
            _CACHE_VERSAO_BANCO[db_url] = int(str(versao_raw).split('.')[0])

        return _CACHE_VERSAO_BANCO[db_url]

    except Exception as e:
        print(f"Aviso ao consultar versão do MySQL: {e}")
        return 5  # Fallback seguro para sintaxe legada em caso de falha
# =========================+----------------------------+========================================

# consulta da empresa
def ConsultaEmpresa(db):
    try:
        resultado = db.execute(
            text("SELECT * FROM cadempresa  ")
        ).fetchone()
    except Exception as e:
        traceback.print_exc()
    return resultado


def ConsultaProdutoCatalogo(db):
    """
    Consulta produtos na tabela cadproduto.

    """
    try:
        sql = "SELECT * FROM cadproduto WHERE situacaoregistro <> 'E' "



        resultado = db.execute(text(sql)).fetchall()
       # logger.warning("Resultado: %s", resultado)
        return resultado

    except Exception as e:
        traceback.print_exc()
        return []

def ConsultaProduto(db, filtro_data: Optional[str] = None):
    try:
        sql_str = """
            SELECT
                empresa,
                codigo,
                descricao,
                unidadeMedida,
                codigobarra,
                agrupamento,
                marca,
                modelo,
                tamanho,
                cor,
                peso,
                precovenda,
                percentualdesconto,
                estoque,
                reajustacondicaopagamento,
                percentualComissao,
                situacaoregistro,
                dataRegistro,
                versao,
                imagens
            FROM cadproduto
        """

        params = {}

        # aplica filtro apenas se houver last_sync
        if filtro_data:
            filtro = datetime.strptime(filtro_data, "%Y-%m-%d %H:%M:%S")
            sql_str += " WHERE dataRegistro >= :filtro_data"
            params["filtro_data"] = filtro

        sql = text(sql_str)
        resultado = db.execute(sql, params).mappings().all()

        logging.warning("📊 Total de produtos retornados: %d", len(resultado))
        if resultado:
            logging.warning("🧾 Exemplo de produto retornado: %s", resultado[0])

        return resultado

    except Exception as e:
        traceback.print_exc()
        logging.error("❌ Erro na consulta de produtos: %s", str(e))
        return []






def ConsultarListaProduto(db):
    """
    Consulta produtos na tabela cadproduto.
    Se filtro_data for fornecido (datetime), retorna apenas produtos
    com dataRegistro > filtro_data.
    """
    try:
        sql = """
            SELECT
                empresa,
                codigo,
                descricao,
                unidadeMedida,
                codigobarra,
                agrupamento,
                marca,
                modelo,
                tamanho,
                cor,
                peso,
                precovenda,               
                percentualdesconto,
                estoque,
                reajustacondicaopagamento,
                percentualComissao,
                situacaoregistro,
                dataRegistro,
                versao,
                imagens
            FROM cadproduto
            WHERE situacaoregistro <> 'E' ORDER BY trim(descricao)
        """

        resultado = db.execute(text(sql)).fetchall()
        return resultado

    except Exception as e:
        traceback.print_exc()
        return []



# consulta da parâmetros
def ConsultaParametro(db):
    try:
        resultado = db.execute(
            text("SELECT * FROM cadparametro  ")
        ).fetchall()
    except Exception as e:
        traceback.print_exc()
    return resultado

def ConsultaParametroporempresa(db):
    """
    Retorna a última data registrada na coluna datacatalogo da tabela cadparametro.
    """
    sql = text("SELECT datacatalogo FROM cadparametro ORDER BY datacatalogo DESC LIMIT 1")
    resultado = db.execute(sql).fetchone()
    if resultado:
        return {"datacatalogo": resultado[0]}
    return None


def AtualizarParametro(db, nome_parametro: str, datacatalogo: datetime):
    print(datacatalogo)
    """
    Atualiza o valor de um parâmetro DATETIME na tabela cadparametro.

    Args:
        db (Session): sessão do banco de dados (controle ou empresa).
        nome_parametro (str): nome do parâmetro a atualizar (ex: 'datacatalogo').
        valor (datetime): novo valor a ser atribuído.
    """
    try:
        sql = text("""
            UPDATE cadparametro
            SET datacatalogo = :datacatalogo  
            WHERE empresa = 1          
        """)
        db.execute(sql, {"datacatalogo": datacatalogo})
        db.commit()
        print(f"Parâmetro '{nome_parametro}' atualizado para: {datacatalogo}")
    except Exception as e:
        db.rollback()
        print(f"Erro ao atualizar parâmetro '{nome_parametro}': {e}")
        raise e

# consulta da rota de cliente
def ConsultaRotaCliente(db):
    try:
        resultado = db.execute(
            text("SELECT * FROM cadrotacliente  ")
        ).fetchall()
    except Exception as e:
        traceback.print_exc()
    return resultado

def ConsultaCliente(db, filtro_data: Optional[str] = None):
    try:
        sql = text("""
            SELECT
                empresa,
                codigo,
                codigovendedor,
                nome,
                contato,
                cpfCnpj,
                rua,
                numero,
                bairro,
                cidade,
                estado,
                telefone,
                limiteCredito,
                observacao,
                restricao,
                reajuste,
                situacaoRegistro,
                dataRegistro,
                versao
            FROM cadcliente
        """)

        params = {}
        if filtro_data:
            sql = text(str(sql) + " WHERE dataRegistro >= :filtro_data")
            # transforma string em datetime antes de mandar pro banco
            filtro = datetime.strptime(filtro_data, "%Y-%m-%d %H:%M:%S")
            params["filtro_data"] = filtro

        resultado = db.execute(sql, params).mappings().all()

        logging.warning("📊 Total de clientes retornados: %d", len(resultado))
        if resultado:
            logging.warning("🧾 Exemplo de cliente retornado: %s", resultado[0])

        return resultado

    except Exception as e:
        traceback.print_exc()
        logging.error("❌ Erro na consulta de clientes: %s", str(e))
        return []


# consulta de vendedores
def ConsultaVendedor(db, filtro_data: Optional[datetime] = None):
    """
    Consulta vendedores na tabela cadvendedor.
    Se filtro_data for fornecido, retorna apenas vendedores com dataRegistro > filtro_data.
    """
    try:
        sql = "SELECT * FROM cadvendedor"
        params = {}

        if filtro_data:
            filtro_str = filtro_data.strftime("%Y-%m-%d %H:%M:%S")  # string compatível com SQL
            sql += " WHERE dataRegistro > :filtro_data"
            params["filtro_data"] = filtro_str

        resultado = db.execute(text(sql), params).mappings().all()
        print("📊 Total de vendedores retornados:", len(resultado))
        if resultado:
            print("🧾 Exemplo de vendedor retornado:", resultado[0])

        return resultado
    except Exception as e:
        traceback.print_exc()
        print("❌ Erro na consulta de vendedores:", str(e))
        return []




def ConsultaCondicoesPagamento(db, filtro_data: Optional[datetime] = None):
    """
    Consulta condições de pagamento na tabela cadcondicaopagamento.
    Se filtro_data for fornecido (datetime), retorna apenas registros
    com dataRegistro >= filtro_data e situacaoRegistro <> 'E'.
    """
    try:
        sql = """
            SELECT
                empresa,
                codigo,
                descricao,
                acrescimo,
                desconto,
                situacaoRegistro,
                dataRegistro               
            FROM cadcondicaopagamento             
        """
        params = {}
        if filtro_data:
            sql += " WHERE dataRegistro >= :filtro_data"
            params["filtro_data"] = filtro_data.strftime("%Y-%m-%d %H:%M:%S")

        resultado = db.execute(text(sql), params).mappings().all()
        logging.warning("📊 Total de condições de pagamento retornadas: %d", len(resultado))
        if resultado:
            logging.warning("🧾 Exemplo de condição retornada: %s", resultado[0])
        return resultado

    except Exception as e:
        traceback.print_exc()
        logging.error("❌ Erro na consulta de condições de pagamento: %s", str(e))
        return []



def Consultar_vendedor_user(db):
    try:
        resultado = db.execute(
            text('''
                SELECT v.codigo, v.nome
                FROM cadvendedor v
                WHERE v.situacaoregistro <> "E"
                  AND v.codigo NOT IN (SELECT u.codigovendedor FROM cadusers u)
                ORDER BY v.nome ASC
            ''')
        ).mappings().all()
        return resultado
    except Exception as e:
        traceback.print_exc()
        return []


def ConsultaVendedores(db):
    try:
        resultado = db.execute(
            text('SELECT codigo, nome FROM cadvendedor '
                 'WHERE situacaoregistro <> "E" '
                 'ORDER BY nome ASC')
        ).mappings().all()
       # print(resultado)
        return resultado
    except Exception as e:
        traceback.print_exc()
        return []

def inserir_usuario(db, empresa_id: int, vendedor_id: str, usuario: str, email: str, senha_hash: str, token: str) -> bool:
    try:
        sql_insert = text("""
            INSERT INTO cadusers 
            (empresa, codigovendedor, usuario, email, senha, novasenha, token, situacaoregistro, dataregistro)
            VALUES (:empresa, :codigovendedor, :usuario, :email, :senha, :novasenha, :token, 'I', NOW())
        """)
        db.execute(sql_insert, {
            "empresa": empresa_id,
            "codigovendedor": vendedor_id,
            "usuario": usuario,
            "email": email,
            "senha": senha_hash,
            "novasenha": senha_hash,
            "token": token
        })
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Erro ao inserir usuário: {e}")
        return False




def ConsultaEmpresaPorCNPJ(db, cnpj: str):
    Format_CNPJ = formata_cnpj(cnpj).strip()
    print("FORMATANDO CNPJ", Format_CNPJ)
    try:
        sql = text("""
            SELECT * 
            FROM cadempresa 
            WHERE cnpj = :cnpj        
        """)
        resultado = db.execute(sql, {"cnpj": Format_CNPJ}).mappings().all()
      # logger.warning("Exibe Resultado da EMPRESA: %s", resultado)
        return resultado
    except Exception as e:
        traceback.print_exc()
        return None


def Consultausers(db):
    try:
        sql = text("""
            SELECT * 
            FROM cadusers 
            WHERE situacaoregistro <> 'E'        
        """)
        resultado = db.execute(sql).mappings().all()
        return resultado
    except Exception as e:
        traceback.print_exc()
        return None

def usuario_existe(db, usuario):
    resultado = db.execute(
        text("SELECT COUNT(*) FROM cadusers WHERE usuario = :usuario and situacaoregistro <> 'E' "),
        {"usuario": usuario}
    ).scalar()
    return resultado > 0

def ConsultaUsuarioPorUsername(db, usuario):
    try:
        sql = text("""
            SELECT * 
            FROM cadusers 
            WHERE situacaoregistro <> 'E'  AND usuario = :usuario       
        """)
        resultado = db.execute(sql, {"usuario": usuario}).mappings().all()
        return resultado
        print(resultado)
    except Exception as e:
        traceback.print_exc()
        return None

def atualizar_senha_usuario(db, usuario, hash):
    dataatual = datetime.now()
    try:
        sql = text("""
            UPDATE cadusers
            SET senha = :novasenha, novasenha = :novasenha, dataregistro = :dataregistro
            WHERE situacaoregistro <> 'E' AND usuario = :usuario
        """)

        resultado = db.execute(sql, {
            "usuario": usuario,
            "novasenha": hash,
            "dataregistro": dataatual
        })

        db.commit()  # 🔑 garante que a alteração seja persistida

        # retorna True se pelo menos 1 linha foi atualizada
        return resultado.rowcount > 0
    except Exception as e:
        traceback.print_exc()
        return None

# Recuperar o usuário
def ConsultaUsuarioPorVendedor(db, vendedor):

  #  logger.warning("Monstra o vendedor: ", vendedor)
    try:
  #      logger.warning("Vendedor recebido na função:", repr(vendedor))
        sql = text("""
            SELECT usuario, email 
            FROM cadusers 
            WHERE situacaoregistro <> 'E' AND codigovendedor = :vendedor       
        """)
        resultado = db.execute(sql, {"vendedor": vendedor}).mappings().all()
      #  print("Resultado da query:", resultado)
        return resultado
    except Exception as e:
        traceback.print_exc()
        return None

from sqlalchemy import text
from datetime import datetime

def inserir_pedido(db, nota):
    try:
        try:
            data_atual = datetime.now(ZoneInfo("America/Sao_Paulo"))
        except Exception:
            data_atual = datetime.now()

        data_formatada = data_atual.strftime("%Y-%m-%d %H:%M:%S")

        # print("Entrou na rotina de inserção")

        # 🔹 Gera o próximo numerodocumento
        result = db.execute(
            text("SELECT COALESCE(MAX(numerodocumento),0)+1 AS prox FROM movnota WHERE empresa=:empresa"),
            {"empresa": nota["empresa"]}
        ).mappings().fetchone()
        prox_numerodoc = result["prox"] if result else 1
      #  print("Numerodocumento gerado:", prox_numerodoc)

        # 🔹 Inserir movnota (incluindo pedido_hash)
        sql_insert_nota = text("""
            INSERT INTO movnota
            (empresa, numerodocumento, codigocondPagamento, codigovendedor, codigocliente,
             nomecliente, idpedido, valorDesconto, valorDespesas, valorFrete,
             valorTotal, pesoTotal, observacao, status, dataLancamento, situacaoRegistro, dataRegistro, pedido_hash)
            VALUES
            (:empresa, :numerodocumento, :codigocondPagamento, :codigovendedor, :codigocliente,
             :nomecliente, :idpedido, :valorDesconto, :valorDespesas, :valorFrete,
             :valorTotal, :pesoTotal, :observacao, :status, :dataLancamento, :situacaoRegistro, :dataRegistro, :pedido_hash)
        """)

        result_nota = db.execute(sql_insert_nota, {
            "empresa": nota["empresa"],
            "numerodocumento": prox_numerodoc,
            "codigocondPagamento": nota.get("codigocondPagamento"),
            "codigovendedor": nota.get("codigovendedor"),
            "codigocliente": nota.get("codigocliente"),
            "nomecliente": nota.get("nomecliente"),
            "idpedido": nota.get("idpedido"),
            "valorDesconto": nota.get("valorDesconto", 0),
            "valorDespesas": nota.get("valorDespesas", 0),
            "valorFrete": nota.get("valorFrete", 0),
            "valorTotal": nota.get("valorTotal", 0),
            "pesoTotal": nota.get("pesoTotal", 0),
            "observacao": nota.get("observacao", ""),
            "status": nota.get("status", "P"),
            "dataLancamento": nota.get("dataLancamento"),
            "situacaoRegistro": nota.get("situacaoRegistro", "I"),
            "dataRegistro": data_formatada,
            "pedido_hash": nota.get("pedido_hash")  # <- aqui grava o hash
        })

        movnota_id = result_nota.lastrowid
     #   print("movnota_id gerado:", movnota_id)

        # 🔹 Inserir itens vinculando movnota_id
        for item in nota.get("itens", []):
            sql_insert_item = text("""
                INSERT INTO movnotaitem
                (empresa, numerodocumento, codigovendedor, codigoproduto, idpedido, descricaoproduto,
                 valorUnitario, valorunitariovenda, valorDesconto, valoracrescimo, valorTotal,
                 quantidade, codigocliente, dataRegistro, situacaoRegistro, movnota_id)
                VALUES
                (:empresa, :numerodocumento, :codigovendedor, :codigoproduto, :idpedido, :descricaoproduto,
                 :valorUnitario, :valorunitariovenda, :valorDesconto, :valoracrescimo, :valorTotal,
                 :quantidade, :codigocliente, :dataRegistro, :situacaoRegistro, :movnota_id)
            """)
            db.execute(sql_insert_item, {
                "empresa": item["empresa"],
                "numerodocumento": prox_numerodoc,
                "codigovendedor": item.get("codigovendedor"),
                "codigoproduto": item.get("codigoproduto"),
                "idpedido": nota.get("idpedido"),
                "descricaoproduto": item.get("descricaoproduto"),
                "valorUnitario": item.get("valorUnitario"),
                "valorunitariovenda": item.get("valorunitariovenda"),
                "valorDesconto": item.get("valorDesconto", 0),
                "valoracrescimo": item.get("valoracrescimo", 0),
                "valorTotal": item.get("valorTotal"),
                "quantidade": item.get("quantidade"),
                "codigocliente": item.get("codigocliente"),
                "dataRegistro": data_formatada,
                "situacaoRegistro": item.get("situacaoRegistro", "I"),
                "movnota_id": movnota_id
            })

        db.commit()
   #     print("Pedido inserido com sucesso:", prox_numerodoc)
        return prox_numerodoc

    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao inserir pedido {nota.get('idpedido')}: {e}")
        return None



def proximo_codigo(db, empresa: int) -> int:
    result = db.execute(
        text("SELECT COALESCE(MAX(numerodocumento),0)+1 AS prox FROM movnota WHERE empresa=:empresa"),
        {"empresa": empresa}
    ).mappings().fetchone()
#    print("Resultado proximo nro: ", result)
    return result["prox"] if result else 1


def Insert_Cliente(db, clientes: List) -> dict:
    """
    Insere/Atualiza clientes em lote e retorna as estatísticas do processamento.
    """
    total_clientes = len(clientes) if clientes else 0
    estatisticas = {
        "sucesso": True,
        "total": total_clientes,
        "inseridos": 0,
        "atualizados": 0,
        "sem_alteracao": 0,
        "tempo_execucao": 0.0
    }

    if not clientes:
        logging.info("ℹ️ Nenhum cliente recebido para gravação.")
        return estatisticas

    tempo_inicio_total = time.time()
    logging.info(f"🚀 [INÍCIO] Processando upsert de {total_clientes} cliente(s)...")

    try:
        # 1. Prepara a lista em memória
        inicio_prep = time.time()
        lista_clientes_dict = [
            {
                **(c.model_dump() if hasattr(c, 'model_dump') else c.dict()),
                'dataRegistro': converter_data_mysql(c.dataRegistro),
                'versao': getattr(c, 'versao', None) if getattr(c, 'versao', None) is not None else 1
            }
            for c in clientes
        ]
        tempo_prep = time.time() - inicio_prep
        logging.info(f"📦 Preparação dos dicionários concluída em {tempo_prep:.2f}s.")

        # 2. Busca versão do cache
        versao_mysql = obter_versao_major_mysql(db)
        logging.info(f"🗄️ Versão do MySQL identificada: {versao_mysql}")

        # 3. Define a query compatível
        if versao_mysql >= 8:
            sql_upsert = text("""
                              INSERT INTO cadcliente (empresa, codigo, codigovendedor, nome, contato, cpfCnpj,
                                                      rua, numero, bairro, cidade, estado, telefone,
                                                      limiteCredito, observacao, restricao, reajuste,
                                                      situacaoRegistro, dataRegistro, versao)
                              VALUES (:empresa, :codigo, :codigovendedor, :nome, :contato, :cpfCnpj,
                                      :rua, :numero, :bairro, :cidade, :estado, :telefone,
                                      :limiteCredito, :observacao, :restricao, :reajuste,
                                      :situacaoRegistro, :dataRegistro, :versao) AS new_row
                              ON DUPLICATE KEY
                              UPDATE
                                  codigovendedor = new_row.codigovendedor,
                                  nome = new_row.nome,
                                  contato = new_row.contato,
                                  cpfCnpj = new_row.cpfCnpj,
                                  rua = new_row.rua,
                                  numero = new_row.numero,
                                  bairro = new_row.bairro,
                                  cidade = new_row.cidade,
                                  estado = new_row.estado,
                                  telefone = new_row.telefone,
                                  limiteCredito = new_row.limiteCredito,
                                  observacao = new_row.observacao,
                                  restricao = new_row.restricao,
                                  reajuste = new_row.reajuste,
                                  situacaoRegistro = new_row.situacaoRegistro,
                                  dataRegistro = new_row.dataRegistro,
                                  versao = new_row.versao
                              """)
        else:
            sql_upsert = text("""
                              INSERT INTO cadcliente (empresa, codigo, codigovendedor, nome, contato, cpfCnpj,
                                                      rua, numero, bairro, cidade, estado, telefone,
                                                      limiteCredito, observacao, restricao, reajuste,
                                                      situacaoRegistro, dataRegistro, versao)
                              VALUES (:empresa, :codigo, :codigovendedor, :nome, :contato, :cpfCnpj,
                                      :rua, :numero, :bairro, :cidade, :estado, :telefone,
                                      :limiteCredito, :observacao, :restricao, :reajuste,
                                      :situacaoRegistro, :dataRegistro, :versao) ON DUPLICATE KEY
                              UPDATE
                                  codigovendedor =
                              VALUES (codigovendedor), nome =
                              VALUES (nome), contato =
                              VALUES (contato), cpfCnpj =
                              VALUES (cpfCnpj), rua =
                              VALUES (rua), numero =
                              VALUES (numero), bairro =
                              VALUES (bairro), cidade =
                              VALUES (cidade), estado =
                              VALUES (estado), telefone =
                              VALUES (telefone), limiteCredito =
                              VALUES (limiteCredito), observacao =
                              VALUES (observacao), restricao =
                              VALUES (restricao), reajuste =
                              VALUES (reajuste), situacaoRegistro =
                              VALUES (situacaoRegistro), dataRegistro =
                              VALUES (dataRegistro), versao =
                              VALUES (versao)
                              """)

        # 4. Inserção em blocos (chunking) e contagem dos afazeres
        CHUNK_SIZE = 500
        total_lotes = (total_clientes + CHUNK_SIZE - 1) // CHUNK_SIZE
        logging.info(f"⏳ Iniciando envio para o banco em {total_lotes} lote(s) de até {CHUNK_SIZE} registros...")

        for index, i in enumerate(range(0, total_clientes, CHUNK_SIZE), start=1):
            tempo_lote_inicio = time.time()
            chunk = lista_clientes_dict[i:i + CHUNK_SIZE]

            # Executa o lote
            result = db.execute(sql_upsert, chunk)

            # Contabiliza registros inseridos vs atualizados
            if hasattr(result, 'rowcount') and result.rowcount is not None:
                # No MySQL ON DUPLICATE KEY: rowcount total do lote reflete
                # (1 * inseridos) + (2 * atualizados)
                # Para obter a divisão por item, o ideal é contar via estatística do driver ou lote
                pass

            tempo_lote = time.time() - tempo_lote_inicio
            processados = min(i + CHUNK_SIZE, total_clientes)
            porcentagem = (processados / total_clientes) * 100

            logging.info(
                f"  ➡️ Lote {index}/{total_lotes} | Processados: {processados}/{total_clientes} "
                f"({porcentagem:.1f}%) | Tempo deste lote: {tempo_lote:.2f}s"
            )

        # 5. Commit no banco
        tempo_commit_inicio = time.time()
        db.commit()
        tempo_commit = time.time() - tempo_commit_inicio
        logging.info(f"💾 Commit executado com sucesso em {tempo_commit:.2f}s.")

        tempo_total = time.time() - tempo_inicio_total
        estatisticas["tempo_execucao"] = round(tempo_total, 2)

        logging.info(f"✅ [SUCESSO] Finalizada gravação de {total_clientes} clientes em {tempo_total:.2f}s!")
        return estatisticas

    except Exception as e:
        db.rollback()
        logging.error(f"❌ [ERRO] Falha ao processar gravações de clientes: {e}", exc_info=True)
        estatisticas["sucesso"] = False
        return estatisticas


def Insert_Produto(db, produtos: List) -> dict:
    """
    Insere/Atualiza produtos em lote no banco de dados usando o schema Pydantic ProdutoCreate.
    """
    total_produtos = len(produtos) if produtos else 0
    estatisticas = {
        "sucesso": True,
        "total": total_produtos,
        "tempo_execucao": 0.0
    }

    if not produtos:
        logging.info("ℹ️ Nenhum produto recebido para gravação.")
        return estatisticas

    tempo_inicio_total = time.time()
    logging.info(f"🚀 [INÍCIO] Processando upsert de {total_produtos} produto(s)...")

    try:
        # 1. Prepara dicionários em memória extraindo do ProdutoCreate / ProdutoBase
        inicio_prep = time.time()

        lista_produtos_dict = []
        for p in produtos:
            # Obtém o dicionário do Pydantic v2
            p_dict = p.model_dump() if hasattr(p, 'model_dump') else p.dict()

            # Formata data para o MySQL
            p_dict['dataRegistro'] = converter_data_mysql(p.dataRegistro)

            # Converte Decimals para float se a model do SQLAlchemy estiver usando Float
            for campo in ['peso', 'precoVenda', 'percentualDesconto', 'estoque', 'percentualComissao']:
                if p_dict.get(campo) is not None:
                    p_dict[campo] = float(p_dict[campo])

            lista_produtos_dict.append(p_dict)

        tempo_prep = time.time() - inicio_prep
        logging.info(f"📦 Dicionários de produtos preparados em {tempo_prep:.2f}s.")

        # 2. Busca versão do MySQL
        versao_mysql = obter_versao_major_mysql(db)

        # 3. Define a instrução SQL com suporte a versao e imagens
        if versao_mysql >= 8:
            sql_upsert = text("""
                              INSERT INTO cadproduto (empresa, codigo, descricao, unidadeMedida, codigoBarra,
                                                      agrupamento, marca, modelo, tamanho, cor, peso, 
                                                      precoVenda, percentualDesconto, estoque, 
                                                      reajustaCondicaoPagamento, percentualComissao,
                                                      situacaoRegistro, dataRegistro, versao, imagens)
                              VALUES (:empresa, :codigo, :descricao, :unidadeMedida, :codigoBarra,
                                      :agrupamento, :marca, :modelo, :tamanho, :cor, :peso, 
                                      :precoVenda, :percentualDesconto, :estoque, 
                                      :reajustaCondicaoPagamento, :percentualComissao,
                                      :situacaoRegistro, :dataRegistro, :versao, :imagens) AS new_row
                              ON DUPLICATE KEY
                              UPDATE
                                  descricao = new_row.descricao,
                                  unidadeMedida = new_row.unidadeMedida,
                                  codigoBarra = new_row.codigoBarra,
                                  agrupamento = new_row.agrupamento,
                                  marca = new_row.marca,
                                  modelo = new_row.modelo,
                                  tamanho = new_row.tamanho,
                                  cor = new_row.cor,
                                  peso = new_row.peso,
                                  precoVenda = new_row.precoVenda,
                                  percentualDesconto = new_row.percentualDesconto,
                                  estoque = new_row.estoque,
                                  reajustaCondicaoPagamento = new_row.reajustaCondicaoPagamento,
                                  percentualComissao = new_row.percentualComissao,
                                  situacaoRegistro = new_row.situacaoRegistro,
                                  dataRegistro = new_row.dataRegistro,
                                  versao = new_row.versao,
                                  imagens = new_row.imagens
                              """)
        else:
            sql_upsert = text("""
                              INSERT INTO cadproduto (empresa, codigo, descricao, unidadeMedida, codigoBarra,
                                                      agrupamento, marca, modelo, tamanho, cor, peso, 
                                                      precoVenda, percentualDesconto, estoque, 
                                                      reajustaCondicaoPagamento, percentualComissao,
                                                      situacaoRegistro, dataRegistro, versao, imagens)
                              VALUES (:empresa, :codigo, :descricao, :unidadeMedida, :codigoBarra,
                                      :agrupamento, :marca, :modelo, :tamanho, :cor, :peso, 
                                      :precoVenda, :percentualDesconto, :estoque, 
                                      :reajustaCondicaoPagamento, :percentualComissao,
                                      :situacaoRegistro, :dataRegistro, :versao, :imagens) ON DUPLICATE KEY
                              UPDATE
                                  descricao = VALUES (descricao), 
                                  unidadeMedida = VALUES (unidadeMedida), 
                                  codigoBarra = VALUES (codigoBarra), 
                                  agrupamento = VALUES (agrupamento), 
                                  marca = VALUES (marca), 
                                  modelo = VALUES (modelo), 
                                  tamanho = VALUES (tamanho), 
                                  cor = VALUES (cor), 
                                  peso = VALUES (peso), 
                                  precoVenda = VALUES (precoVenda), 
                                  percentualDesconto = VALUES (percentualDesconto), 
                                  estoque = VALUES (estoque), 
                                  reajustaCondicaoPagamento = VALUES (reajustaCondicaoPagamento), 
                                  percentualComissao = VALUES (percentualComissao), 
                                  situacaoRegistro = VALUES (situacaoRegistro), 
                                  dataRegistro = VALUES (dataRegistro), 
                                  versao = VALUES (versao),
                                  imagens = VALUES (imagens)
                              """)

        # 4. Inserção em blocos (chunking)
        CHUNK_SIZE = 500
        total_lotes = (total_produtos + CHUNK_SIZE - 1) // CHUNK_SIZE
        logging.info(f"⏳ Gravando produtos em {total_lotes} lote(s)...")

        for index, i in enumerate(range(0, total_produtos, CHUNK_SIZE), start=1):
            tempo_lote_inicio = time.time()
            chunk = lista_produtos_dict[i:i + CHUNK_SIZE]

            db.execute(sql_upsert, chunk)

            tempo_lote = time.time() - tempo_lote_inicio
            processados = min(i + CHUNK_SIZE, total_produtos)
            porcentagem = (processados / total_produtos) * 100

            logging.info(
                f"  ➡️ Lote {index}/{total_lotes} | Processados: {processados}/{total_produtos} "
                f"({porcentagem:.1f}%) | Tempo deste lote: {tempo_lote:.2f}s"
            )

        # 5. Commit no banco
        tempo_commit_inicio = time.time()
        db.commit()
        tempo_commit = time.time() - tempo_commit_inicio
        logging.info(f"💾 Commit executado com sucesso em {tempo_commit:.2f}s.")

        tempo_total = time.time() - tempo_inicio_total
        estatisticas["tempo_execucao"] = round(tempo_total, 2)

        logging.info(f"✅ [SUCESSO] Finalizada gravação de {total_produtos} produtos em {tempo_total:.2f}s!")
        return estatisticas

    except Exception as e:
        db.rollback()
        logging.error(f"❌ [ERRO] Falha ao processar gravações de produtos: {e}", exc_info=True)
        estatisticas["sucesso"] = False
        return estatisticas

def Insert_Vendedor(db, vendedor):
    try:
        dados = vendedor.model_dump() if hasattr(vendedor, 'model_dump') else vendedor.dict()
        logger.info(f"🔄 Processando Vendedor: Empresa={vendedor.empresa}, Codigo={vendedor.codigo}")

        sql_select = text("SELECT 1 FROM cadvendedor WHERE empresa = :empresa AND codigo = :codigo")
        existe = db.execute(sql_select, {"empresa": vendedor.empresa, "codigo": vendedor.codigo}).fetchone()

        if existe:
            logger.info(f"✏️ Atualizando vendedor existente (Empresa={vendedor.empresa}, Codigo={vendedor.codigo})")
            sql_update = text("""
                UPDATE cadvendedor SET
                    cd_rota = :cd_rota,
                    nome = :nome,
                    situacaoRegistro = :situacaoRegistro,
                    dataRegistro = :dataRegistro,
                    limitedesconto = :limitedesconto,
                    versao = :versao
                WHERE empresa = :empresa AND codigo = :codigo
            """)
            db.execute(sql_update, dados)
        else:
            logger.info(f"➕ Inserindo novo vendedor (Empresa={vendedor.empresa}, Codigo={vendedor.codigo})")
            sql_insert = text("""
                INSERT INTO cadvendedor (
                    empresa, codigo, cd_rota, nome,
                    situacaoRegistro, dataRegistro, limitedesconto, versao
                ) VALUES (
                    :empresa, :codigo, :cd_rota, :nome,
                    :situacaoRegistro, :dataRegistro, :limitedesconto, :versao
                )
            """)
            db.execute(sql_insert, dados)

        db.commit()
        logger.info(f"✅ Vendedor {vendedor.codigo} salvo com sucesso.")
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"💥 ERRO NO BANCO DE DADOS ao processar vendedor {getattr(vendedor, 'codigo', 'UNKNOWN')}:")
        logger.error(f"--> Tipo da Exceção: {e.__class__.__name__}")
        logger.error(f"--> Mensagem: {str(e)}")
        return False

def Insert_Condicao_Pagamento(db, condicao):
    try:
        sql_select = text("SELECT 1 FROM cadcondicaopagamento WHERE empresa = :empresa AND codigo = :codigo")
        existe = db.execute(sql_select, {"empresa": condicao.empresa, "codigo": condicao.codigo}).fetchone()

        if existe:
            sql_update = text("""
            UPDATE cadcondicaopagamento SET
                descricao = :descricao,
                acrescimo = :acrescimo,
                desconto = :desconto,
                situacaoRegistro = :situacaoRegistro,
                dataRegistro = :dataRegistro
            WHERE empresa = :empresa AND codigo = :codigo
            """)
            db.execute(sql_update, condicao.dict())
        else:
            # Incluído o campo 'versao' com valor inicial 1
            sql_insert = text("""
            INSERT INTO cadcondicaopagamento (
                empresa, codigo, descricao, acrescimo, desconto,
                situacaoRegistro, dataRegistro, versao
            ) VALUES (
                :empresa, :codigo, :descricao, :acrescimo, :desconto,
                :situacaoRegistro, :dataRegistro, 1
            )
            """)
            db.execute(sql_insert, condicao.dict())

        db.commit()
        return True

    except Exception as e:
        print(f"Erro ao inserir/atualizar condição de pagamento: {e}")
        db.rollback()
        return False

def Insert_Parametro(db, parametro):
    try:
        # Verifica se já existe parâmetro para a empresa
        sql_select = "SELECT 1 FROM parametros WHERE empresa = :empresa"
        existe = db.execute(sql_select, {"empresa": parametro.empresa}).fetchone()

        if existe:
            # Atualiza registro existente
            sql_update = """
            UPDATE parametros SET
                vendedorPadrao = :vendedorPadrao,              
                controlaSaldoEstoque = :controlaSaldoEstoque,
                casaDecimalQuantidade = :casaDecimalQuantidade,
                casaDecimalValor = :casaDecimalValor,               
                percentualDescontoVenda = :percentualDescontoVenda,                
                situacaoRegistro = :situacaoRegistro,
                dataRegistro = :dataRegistro
               
            WHERE empresa = :empresa
            """
            db.execute(sql_update, parametro.dict())
        else:
            # Insere novo registro
            sql_insert = """
            INSERT INTO parametros (
                empresa, vendedorPadrao,controlaSaldoEstoque,
                casaDecimalQuantidade,
                percentualDescontoVenda, situacaoRegistro, dataRegistro
            ) VALUES (
                :empresa, :vendedorPadrao, :controlaSaldoEstoque,
                :casaDecimalQuantidade, :casaDecimalValor, 
                :percentualDescontoVenda, :situacaoRegistro, :dataRegistro
            )
            """
            db.execute(sql_insert, parametro.dict())

        db.commit()
        return True

    except Exception as e:
        print(f"Erro ao inserir/atualizar parâmetro: {e}")
        db.rollback()
        return False

def Insert_Empresa(db, empresa):
    try:
        # Verifica se já existe empresa com o mesmo código ou CNPJ
        sql_check = "SELECT codigo FROM cadempresa WHERE codigo = :codigo OR cnpj = :cnpj"
        existente = db.execute(sql_check, {"codigo": empresa.codigo, "cnpj": empresa.cnpj}).fetchone()

        if existente:
            # UPDATE
            sql_update = """
            UPDATE cadempresa SET
                nome = :nome,
                cnpj = :cnpj,
                rua = :rua,
                numero = :numero,
                bairro = :bairro,
                cidade = :cidade,
                telefone = :telefone,
                email = :email
            WHERE codigo = :codigo
            """
            db.execute(sql_update, empresa.dict())
        else:
            # INSERT
            sql_insert = """
            INSERT INTO cadempresa (
                codigo, nome, cnpj, rua, numero, bairro, cidade, telefone, email
            ) VALUES (
                :codigo, :nome, :cnpj, :rua, :numero, :bairro, :cidade, :telefone, :email
            )
            """
            db.execute(sql_insert, empresa.dict())

        db.commit()
        return True
    except Exception as e:
        print(f"Erro ao inserir/atualizar empresa: {e}")
        db.rollback()
        return False


