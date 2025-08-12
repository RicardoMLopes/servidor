from sqlalchemy import text
import traceback

from funtions import formata_cnpj


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
            text("SELECT * FROM CadCondicaoPagamento  ")
        ).fetchall()
    except Exception as e:
        traceback.print_exc()
    return resultado


def ConsultaVendedores(db):
    try:
        resultado = db.execute(
            text('SELECT codigo, nome FROM cadvendedor WHERE situacaoregistro <> "E"')
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
            VALUES (:empresa, :codigovendedor, :usuario, :senha, :novasenha, :token, 'ativo', NOW())
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



