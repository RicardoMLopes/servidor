# model/cadproduto_model.py
from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, BigInteger, Float, SmallInteger
from sqlalchemy.orm import declarative_base
from datetime import datetime

p_Base = declarative_base()

class CadProduto(p_Base):
    __tablename__ = "cadproduto"

    id = Column(Integer, primary_key=True, autoincrement=True)
    empresa = Column(Integer, nullable=False)
    codigo = Column(String(6), nullable=False)
    descricao = Column(String(500), nullable=False)
    unidadeMedida = Column(String(3))
    codigoBarra = Column(String(20))
    agrupamento = Column(String(60))
    marca = Column(String(60))
    modelo = Column(String(60))
    tamanho = Column(String(20))
    cor = Column(String(20))
    peso = Column(Float(15), default=0.0)
    precoVenda = Column(Float(15), default=0.0)
    percentualDesconto = Column(Float(15), default=0.0)
    estoque = Column(Float(15), default=0.0)
    reajustaCondicaoPagamento = Column(String(1), default="N")
    percentualComissao = Column(Float(15), default=0.0)
    situacaoRegistro = Column(String(1), default="I")
    dataRegistro = Column(DateTime, default=datetime.now, nullable=False)