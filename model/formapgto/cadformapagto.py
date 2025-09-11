from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, BigInteger
from sqlalchemy.orm import declarative_base

f_Base = declarative_base()

class CadCondicaoPagamento(f_Base):
    __tablename__ = "cadcondicaopagamento"

    id = Column(Integer, primary_key=True, autoincrement=True)
    empresa = Column(Integer, nullable=False)
    codigo = Column(String(6), nullable=False)
    descricao = Column(String(40))
    acrescimo = Column(DECIMAL(15,4), default=0)
    desconto = Column(DECIMAL(15,4), default=0)
    situacaoRegistro = Column(String(1), default="I")
    dataRegistro = Column(DateTime)
