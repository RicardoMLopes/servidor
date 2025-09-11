from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, BigInteger
from sqlalchemy.orm import declarative_base

c_Base = declarative_base()

class CadCliente(c_Base):
    __tablename__ = "cadcliente"

    id = Column(Integer, primary_key=True, autoincrement=True)
    empresa = Column(Integer, nullable=False)
    codigo = Column(String(6), nullable=False)
    codigovendedor = Column(String(6), default="0")
    nome = Column(String(250), nullable=False)
    contato = Column(String(250))
    cpfCnpj = Column(String(14))
    rua = Column(String(80))
    numero = Column(String(7))
    bairro = Column(String(80))
    cidade = Column(String(80))
    estado = Column(String(30))
    telefone = Column(String(30))
    limiteCredito = Column(DECIMAL(12,2), default=0)
    observacao = Column(String(500))
    restricao = Column(String(250))
    reajuste = Column(DECIMAL(5,2), default=0)
    situacaoRegistro = Column(String(1), default="A")
    dataRegistro = Column(DateTime)
    versao = Column(BigInteger, default=1)
