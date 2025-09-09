from sqlalchemy import text
import traceback
from typing import Dict, Any, Optional

from params.alerta import enviar_alerta
from function.funtions import formata_cnpj, limpar_texto_mysql_auto, converter_data_mysql
from datetime import datetime

from params.logger_config import logger


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

def ConsultaProduto(db, filtro_data: Optional[datetime] = None):
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
                casasdecimais,
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

        if filtro_data:
            filtro_str = filtro_data.strftime("%Y-%m-%d %H:%M:%S")
            sql += " WHERE dataRegistro > :filtro_data"
            params["filtro_data"] = filtro_str

        resultado = db.execute(text(sql), params).fetchall()
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

# consulta de clientes
def ConsultaCliente(db, filtro_data: Optional[datetime] = None):
    """
    Consulta clientes na tabela cadcliente.
    Se filtro_data for fornecido (datetime), retorna apenas clientes
    com dataRegistro > filtro_data.
    """
    try:
        sql = "SELECT * FROM cadcliente"
        params = {}

        if filtro_data:
            # Formata datetime para string compatível com SQL
            filtro_str = filtro_data.strftime("%Y-%m-%d %H:%M:%S")
            sql += " WHERE dataRegistro > :filtro_data"
            params["filtro_data"] = filtro_str

        resultado = db.execute(text(sql), params).fetchall()
        return resultado

    except Exception as e:
        traceback.print_exc()
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
            # Formata datetime para string compatível com SQL
            filtro_str = filtro_data.strftime("%Y-%m-%d %H:%M:%S")
            sql += " WHERE dataRegistro > :filtro_data"
            params["filtro_data"] = filtro_str

        resultado = db.execute(text(sql), params).fetchall()
        return resultado
    except Exception as e:
        traceback.print_exc()
        return []




# consulta de forma de pagamento
def ConsultaCondicoesPagamento(db, filtro_data: Optional[datetime] = None):
    try:
        sql = "SELECT * FROM cadcondicaopagamento"
        params = {}

        if filtro_data:
            # Formata datetime para string compatível com SQL
            filtro_str = filtro_data.strftime("%Y-%m-%d %H:%M:%S")
            sql += " WHERE dataRegistro > :filtro_data"
            params["filtro_data"] = filtro_str

        resultado = db.execute(text(sql), params).fetchall()
        return resultado
    except Exception as e:
        traceback.print_exc()
        return []



def Consultar_vendedor_user(db):
    try:
        resultado = db.execute(
            text('''
                SELECT v.codigo, v.nome
                FROM cadvendedor v
                WHERE v.situacaoregistro <> "E"
                  AND v.codigo NOT IN (SELECT u.codigovendedor FROM cadusers u)
            ''')
        ).mappings().all()
        return resultado
    except Exception as e:
        traceback.print_exc()
        return []


def ConsultaVendedores(db):
    try:
        resultado = db.execute(
            text('SELECT codigo, nome FROM cadvendedor WHERE situacaoregistro <> "E" ')
        ).mappings().all()
       # print(resultado)
        return resultado
    except Exception as e:
        traceback.print_exc()
        return []

def inserir_usuario(db, empresa_id: int, vendedor_id: str, usuario: str, senha_hash: str, token: str) -> bool:
    try:
        sql_insert = text("""
            INSERT INTO cadusers 
            (empresa, codigovendedor, usuario, senha, novasenha, token, situacaoregistro, dataregistro)
            VALUES (:empresa, :codigovendedor, :usuario, :senha, :novasenha, :token, 'I', NOW())
        """)
        db.execute(sql_insert, {
            "empresa": empresa_id,
            "codigovendedor": vendedor_id,
            "usuario": usuario,
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
    Format_CNPJ = formata_cnpj(cnpj)
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
        print("Resultado da query:", resultado)
        return resultado
    except Exception as e:
        traceback.print_exc()
        return None

from sqlalchemy import text
from datetime import datetime

def inserir_pedido(db, nota):
    try:
        print("Entrou na rotina de inserção")

        # 🔹 Gera o próximo numerodocumento
        result = db.execute(
            text("SELECT COALESCE(MAX(numerodocumento),0)+1 AS prox FROM movnota WHERE empresa=:empresa"),
            {"empresa": nota["empresa"]}
        ).mappings().fetchone()
        prox_numerodoc = result["prox"] if result else 1
        print("Numerodocumento gerado:", prox_numerodoc)

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
            "dataLancamento": datetime.now(),
            "situacaoRegistro": nota.get("situacaoRegistro", "I"),
            "dataRegistro": datetime.now(),
            "pedido_hash": nota.get("pedido_hash")  # <- aqui grava o hash
        })

        movnota_id = result_nota.lastrowid
        print("movnota_id gerado:", movnota_id)

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
                "idpedido": item.get("idpedido"),
                "descricaoproduto": item.get("descricaoproduto"),
                "valorUnitario": item.get("valorUnitario"),
                "valorunitariovenda": item.get("valorunitariovenda"),
                "valorDesconto": item.get("valorDesconto", 0),
                "valoracrescimo": item.get("valoracrescimo", 0),
                "valorTotal": item.get("valorTotal"),
                "quantidade": item.get("quantidade"),
                "codigocliente": item.get("codigocliente"),
                "dataRegistro": datetime.now(),
                "situacaoRegistro": item.get("situacaoRegistro", "I"),
                "movnota_id": movnota_id
            })

        db.commit()
        print("Pedido inserido com sucesso:", prox_numerodoc)
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
    print("Resultado proximo nro: ", result)
    return result["prox"] if result else 1


def Insert_Cliente(db, cliente):
    try:
        cliente_dict = cliente.dict()
        cliente_dict['dataRegistro'] = converter_data_mysql(cliente.dataRegistro)

        # Verifica se já existe cliente com mesmo código e empresa
        sql_select = text("SELECT 1 FROM cadcliente WHERE empresa = :empresa AND codigo = :codigo")
        existe = db.execute(sql_select, {"empresa": cliente_dict['empresa'], "codigo": cliente_dict['codigo']}).fetchone()

        if existe:
            # Atualiza registro existente
            sql_update = text("""
            UPDATE cadcliente SET
                codigovendedor = :codigovendedor,
                nome = :nome,
                contato = :contato,
                cpfCnpj = :cpfCnpj,
                rua = :rua,
                numero = :numero,
                bairro = :bairro,
                cidade = :cidade,
                estado = :estado,
                telefone = :telefone,
                limiteCredito = :limiteCredito,
                observacao = :observacao,
                restricao = :restricao,
                reajuste = :reajuste,
                situacaoRegistro = :situacaoRegistro,
                dataRegistro = :dataRegistro,
                versao = :versao
            WHERE empresa = :empresa AND codigo = :codigo
            """)
            db.execute(sql_update, cliente_dict)  # usar cliente_dict, não cliente.dict()
        else:
            # Insere novo cliente
            sql_insert = text("""
            INSERT INTO cadcliente (
                empresa, codigo, codigovendedor, nome, contato, cpfCnpj,
                rua, numero, bairro, cidade, estado, telefone,
                limiteCredito, observacao, restricao, reajuste,
                situacaoRegistro, dataRegistro, versao
            ) VALUES (
                :empresa, :codigo, :codigovendedor, :nome, :contato, :cpfCnpj,
                :rua, :numero, :bairro, :cidade, :estado, :telefone,
                :limiteCredito, :observacao, :restricao, :reajuste,
                :situacaoRegistro, :dataRegistro, :versao
            )
            """)
            db.execute(sql_insert, cliente_dict)  # também usar cliente_dict

        db.commit()
        return True

    except Exception as e:
        print(f"Erro ao inserir/atualizar cliente: {e}")
        db.rollback()
        return False

def Insert_Produto(db, produto):
    try:
        # Verifica se já existe produto com o mesmo código e empresa
        sql_select = "SELECT 1 FROM cadprodutos WHERE empresa = :empresa AND codigo = :codigo"
        existe = db.execute(sql_select, {"empresa": produto.empresa, "codigo": produto.codigo}).fetchone()

        if existe:
            # Atualiza registro existente
            sql_update = """
            UPDATE cadprodutos SET
                descricao = :descricao,
                unidademedida = :unidademedida,
                codigobarra = :codigobarra,
                agrupamento = :agrupamento,
                marca = :marca,
                modelo = :modelo,
                tamanho = :tamanho,
                cor = :cor,
                peso = :peso,
                precoVenda = :precoVenda,
                casasdecimais = :casasdecimais,
                percentualdesconto = :percentualdesconto,
                estoque = :estoque,
                reajustacondicaopagamento = :reajustacondicaopagamento,
                percentualcomissao = :percentualcomissao,
                situacaoRegistro = :situacaoRegistro,
                dataRegistro = :dataRegistro,
                versao = :versao,
                imagens = :imagens
            WHERE empresa = :empresa AND codigo = :codigo
            """
            db.execute(sql_update, produto.dict())
        else:
            # Insere novo produto
            sql_insert = """
            INSERT INTO cadprodutos (
                empresa, codigo, descricao, unidademedida, codigobarra,
                agrupamento, marca, modelo, tamanho, cor, peso,
                precoVenda, casasdecimais, percentualdesconto, estoque, reajustacondicaopagamento,
                percentualcomissao, situacaoRegistro, dataRegistro, versao, imagens
            ) VALUES (
                :empresa, :codigo, :descricao, :unidademedida, :codigobarra,
                :agrupamento, :marca, :modelo, :tamanho, :cor, :peso,
                :precoVenda, :casasdecimais, :percentualdesconto, :estoque, :reajustacondicaopagamento,
                :percentualcomissao, :situacaoRegistro, :dataRegistro, :versao, :imagens
            )
            """
            db.execute(sql_insert, produto.dict())

        db.commit()
        return True

    except Exception as e:
        print(f"Erro ao inserir/atualizar produto: {e}")
        db.rollback()
        return False

def Insert_Vendedor(db, vendedor):
    try:
        # Verifica se já existe vendedor com mesmo código e empresa
        sql_select = "SELECT 1 FROM vendedores WHERE empresa = :empresa AND codigo = :codigo"
        existe = db.execute(sql_select, {"empresa": vendedor.empresa, "codigo": vendedor.codigo}).fetchone()

        if existe:
            # Atualiza registro existente
            sql_update = """
            UPDATE vendedores SET
                cd_rota = :cd_rota,
                nome = :nome,
                situacaoRegistro = :situacaoRegistro,
                dataRegistro = :dataRegistro,
                versao = :versao
            WHERE empresa = :empresa AND codigo = :codigo
            """
            db.execute(sql_update, vendedor.dict())
        else:
            # Insere novo vendedor
            sql_insert = """
            INSERT INTO vendedores (
                empresa, codigo, cd_rota, nome,
                situacaoRegistro, dataRegistro, versao
            ) VALUES (
                :empresa, :codigo, :cd_rota, :nome,
                :situacaoRegistro, :dataRegistro, :versao
            )
            """
            db.execute(sql_insert, vendedor.dict())

        db.commit()
        return True

    except Exception as e:
        print(f"Erro ao inserir/atualizar vendedor: {e}")
        db.rollback()
        return False

def Insert_Condicao_Pagamento(db, condicao):
    try:
        # Verifica se já existe a condição de pagamento
        sql_select = "SELECT 1 FROM condicoes_pagamento WHERE empresa = :empresa AND codigo = :codigo"
        existe = db.execute(sql_select, {"empresa": condicao.empresa, "codigo": condicao.codigo}).fetchone()

        if existe:
            # Atualiza registro existente
            sql_update = """
            UPDATE condicoes_pagamento SET
                descricao = :descricao,
                acrescimo = :acrescimo,
                desconto = :desconto,
                situacaoRegistro = :situacaoRegistro,
                dataRegistro = :dataRegistro,
                versao = :versao
            WHERE empresa = :empresa AND codigo = :codigo
            """
            db.execute(sql_update, condicao.dict())
        else:
            # Insere novo registro
            sql_insert = """
            INSERT INTO condicoes_pagamento (
                empresa, codigo, descricao, acrescimo, desconto,
                situacaoRegistro, dataRegistro, versao
            ) VALUES (
                :empresa, :codigo, :descricao, :acrescimo, :desconto,
                :situacaoRegistro, :dataRegistro, :versao
            )
            """
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
                atualizaCliente = :atualizaCliente,
                atualizaCondPagamento = :atualizaCondPagamento,
                atualizaParametro = :atualizaParametro,
                atualizaProduto = :atualizaProduto,
                atualizaVendedor = :atualizaVendedor,
                controlaSaldoEstoque = :controlaSaldoEstoque,
                casaDecimalQuantidade = :casaDecimalQuantidade,
                casaDecimalValor = :casaDecimalValor,
                controlaFormaPagamento = :controlaFormaPagamento,
                percentualDescontoVenda = :percentualDescontoVenda,
                mostrarFinanceiro = :mostrarFinanceiro,
                mostrarFinanceiroVencido = :mostrarFinanceiroVencido,
                dataUltimaAtualizacao = :dataUltimaAtualizacao,
                situacaoRegistro = :situacaoRegistro,
                dataRegistro = :dataRegistro,
                versaoGeral = :versaoGeral,
                versaoVendedor = :versaoVendedor,
                versaoCliente = :versaoCliente,
                versaoCondicaoPagamento = :versaoCondicaoPagamento,
                versaoCheckListPergunta = :versaoCheckListPergunta,
                versaoCheckListResposta = :versaoCheckListResposta,
                versaoFinanceiro = :versaoFinanceiro,
                versaoRotaCondicaoPagamento = :versaoRotaCondicaoPagamento,
                versaoRotaCliente = :versaoRotaCliente,
                versaoProduto = :versaoProduto,
                versaoParametro = :versaoParametro
            WHERE empresa = :empresa
            """
            db.execute(sql_update, parametro.dict())
        else:
            # Insere novo registro
            sql_insert = """
            INSERT INTO parametros (
                empresa, vendedorPadrao, atualizaCliente, atualizaCondPagamento,
                atualizaParametro, atualizaProduto, atualizaVendedor, controlaSaldoEstoque,
                casaDecimalQuantidade, casaDecimalValor, controlaFormaPagamento,
                percentualDescontoVenda, mostrarFinanceiro, mostrarFinanceiroVencido,
                dataUltimaAtualizacao, situacaoRegistro, dataRegistro, versaoGeral,
                versaoVendedor, versaoCliente, versaoCondicaoPagamento, versaoCheckListPergunta,
                versaoCheckListResposta, versaoFinanceiro, versaoRotaCondicaoPagamento,
                versaoRotaCliente, versaoProduto, versaoParametro
            ) VALUES (
                :empresa, :vendedorPadrao, :atualizaCliente, :atualizaCondPagamento,
                :atualizaParametro, :atualizaProduto, :atualizaVendedor, :controlaSaldoEstoque,
                :casaDecimalQuantidade, :casaDecimalValor, :controlaFormaPagamento,
                :percentualDescontoVenda, :mostrarFinanceiro, :mostrarFinanceiroVencido,
                :dataUltimaAtualizacao, :situacaoRegistro, :dataRegistro, :versaoGeral,
                :versaoVendedor, :versaoCliente, :versaoCondicaoPagamento, :versaoCheckListPergunta,
                :versaoCheckListResposta, :versaoFinanceiro, :versaoRotaCondicaoPagamento,
                :versaoRotaCliente, :versaoProduto, :versaoParametro
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


