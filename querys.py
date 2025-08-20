from sqlalchemy import text
import traceback
from typing import Dict, Any
from funtions import formata_cnpj, converter_data_mysql, limpar_texto_mysql_generico


# consulta da empresa
def ConsultaEmpresa(db):
    try:
        resultado = db.execute(
            text("SELECT * FROM cadempresa  ")
        ).fetchone()
    except Exception as e:
        traceback.print_exc()
    return resultado

# consulta da lista de produtos
def ConsultaProduto(db):
    try:
        resultado = db.execute(
            text("SELECT * FROM cadproduto  ")
        ).fetchall()
    except Exception as e:
        traceback.print_exc()
    return resultado


# consulta da parâmetros
def ConsultaParametro(db):
    try:
        resultado = db.execute(
            text("SELECT * FROM cadparametro  ")
        ).fetchall()
    except Exception as e:
        traceback.print_exc()
    return resultado

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
def ConsultaCliente(db):
    try:
        resultado = db.execute(
            text("SELECT * FROM cadcliente  ")
        ).fetchall()
    except Exception as e:
        traceback.print_exc()
    return resultado


# consulta de vendedores
def ConsultaVendedor(db):
    try:
        resultado = db.execute(
            text("SELECT * FROM cadvendedor  ")
        ).fetchall()
    except Exception as e:
        traceback.print_exc()
    return resultado

# consulta de forma de pagamento
def ConsultaCondicoesPagamento(db):
    try:
        resultado = db.execute(
            text("SELECT * FROM cadcondicaopagamento  ")
        ).fetchall()
    except Exception as e:
        traceback.print_exc()
    return resultado



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
    except Exception as e:
        traceback.print_exc()
        return None

def atualizar_senha_usuario(db, usuario, hash):
    try:
        sql = text("""
            UPDATE cadusers SET  novasenha = :novasenha 
            WHERE situacaoregistro <> 'E'  AND usuario = :usuario       
        """)
        resultado = db.execute(sql, {"usuario": usuario, "novasenha":hash}).mappings().all()
        return resultado
    except Exception as e:
        traceback.print_exc()
        return None

# Recuperar o usuário
def ConsultaUsuarioPorVendedor(db, vendedor):
    try:
        print("Vendedor recebido na função:", repr(vendedor))
        sql = text("""
            SELECT usuario 
            FROM cadusers 
            WHERE situacaoregistro <> 'E' AND codigovendedor = :vendedor       
        """)
        resultado = db.execute(sql, {"vendedor": vendedor}).mappings().all()
        print("Resultado da query:", resultado)
        return resultado
    except Exception as e:
        traceback.print_exc()
        return None

def inserir_pedido(db, nota: Dict[str, Any]) -> bool:
    """
    Insere uma nota (movnota) e seus itens (movnotaitem) no banco MySQL.
    Toda a operação é feita em uma transação única.
    """
    try:
        # Inicia transação
        db.execute(text("START TRANSACTION"))

        # Gera código para a nota
        print("Entrou na rotina de inserção")
        if "numerodocumento" in nota or nota["numerodocumento"]:
            print("Chamada do proximo numero")
            nota["numerodocumento"] = proximo_codigo(db, nota["empresa"])
        else:
            print("Não entrou na rotina proximo numero")

        # 1️⃣ Inserir cabeçalho
        sql_insert_nota = text("""
            INSERT INTO movnota
            (empresa, numerodocumento, codigocondPagamento, codigovendedor, codigocliente,
             nomecliente, idpedido, valorDesconto, valorDespesas, valorFrete,
             valorTotal, pesoTotal, observacao, status, dataLancamento, situacaoRegistro, dataRegistro)
            VALUES
            (:empresa, :numerodocumento, :codigocondPagamento, :codigovendedor, :codigocliente,
             :nomecliente, :idpedido, :valorDesconto, :valorDespesas, :valorFrete,
             :valorTotal, :pesoTotal, :observacao, :status, :dataLancamento, :situacaoRegistro, :dataRegistro)
        """)

        db.execute(sql_insert_nota, {
            "empresa": nota["empresa"],
            "numerodocumento": nota["numerodocumento"],
            "codigocondPagamento": nota.get("codigocondPagamento", ""),
            "codigovendedor": nota.get("codigovendedor", ""),
            "codigocliente": nota.get("codigocliente", ""),
            "nomecliente": nota.get("nomecliente", ""),
            "idpedido": nota.get("idpedido", 0),
            "valorDesconto": nota.get("valorDesconto", 0),
            "valorDespesas": nota.get("valorDespesas", 0),
            "valorFrete": nota.get("valorFrete", 0),
            "valorTotal": nota.get("valorTotal", 0),
            "pesoTotal": nota.get("pesoTotal", 0),
            "observacao": limpar_texto_mysql_generico(nota.get("observacao", "")),
            "status": nota.get("status", "P"),
            "dataLancamento": nota.get("dataLancamento"),
            "situacaoRegistro": nota.get("situacaoRegistro", "I"),
            "dataRegistro": nota.get("dataRegistro")
        })

        # 2️⃣ Inserir itens
        sql_insert_item = text("""
            INSERT INTO movnotaitem
            (empresa, numerodocumento, codigovendedor, codigoproduto, idpedido, descricaoproduto,
             valorUnitario, valorunitariovenda, valorDesconto, valoracrescimo, valorTotal,
             quantidade, codigocliente, dataRegistro, situacaoRegistro)
            VALUES
            (:empresa, :numerodocumento, :codigovendedor, :codigoproduto, :idpedido, :descricaoproduto,
             :valorUnitario, :valorunitariovenda, :valorDesconto, :valoracrescimo, :valorTotal,
             :quantidade, :codigocliente, :dataRegistro, :situacaoRegistro)
        """)

        for item in nota.get("itens", []):
            db.execute(sql_insert_item, {
                "empresa": item.get("empresa", nota["empresa"]),
                "numerodocumento": nota["numerodocumento"],
                "codigovendedor": item.get("codigovendedor", nota.get("codigovendedor", "")),
                "codigoproduto": item.get("codigoproduto", ""),
                "idpedido": item.get("idpedido", ""),
                "descricaoproduto": item.get("descricaoproduto", ""),
                "valorUnitario": item.get("valorUnitario", 0),
                "valorunitariovenda": item.get("valorunitariovenda", 0),
                "valorDesconto": item.get("valorDesconto", 0),
                "valoracrescimo": item.get("valoracrescimo", 0),
                "valorTotal": item.get("valorTotal", 0),
                "quantidade": item.get("quantidade", 0),
                "codigocliente": item.get("codigocliente", nota.get("codigocliente", "")),
                "dataRegistro": item.get("dataRegistro", nota.get("dataRegistro")),
                "situacaoRegistro": item.get("situacaoRegistro", "I")
            })

        # Finaliza transação
        db.commit()
        return True

    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao inserir pedido {nota.get('numerodocumento', nota.get('codigo'))}: {e}")
        traceback.print_exc()
        return False


def proximo_codigo(db, empresa: int) -> int:
    result = db.execute(
        text("SELECT COALESCE(MAX(numerodocumento),0)+1 AS prox FROM movnota WHERE empresa=:empresa"),
        {"empresa": empresa}
    ).mappings().fetchone()
    print("Resultado proximo nro: ", result)
    return result["prox"] if result else 1





