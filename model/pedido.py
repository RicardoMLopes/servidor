from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.orm import foreign

Base = declarative_base()

class MovNota(Base):
    __tablename__ = "movnota"

    empresa = Column(Integer, primary_key=True)
    numerodocumento = Column(Integer, primary_key=True)
    codigocondPagamento = Column(String(6), nullable=False)
    codigovendedor = Column(String(6), nullable=False)
    codigocliente = Column(String(6), nullable=False)
    nomecliente = Column(String(255))
    idpedido = Column(Integer)
    valorDesconto = Column(Float, default=0.0)
    valorDespesas = Column(Float, default=0.0)
    valorFrete = Column(Float, default=0.0)
    valorTotal = Column(Float, default=0.0)
    pesoTotal = Column(Float, default=0.0)
    observacao = Column(Text)
    status = Column(String(1))
    dataLancamento = Column(DateTime)
    dataRegistro = Column(DateTime)
    situacaoRegistro = Column(String(1), default='I')

    itens = relationship(
        "MovNotaItem",
        back_populates="pedido",
        primaryjoin="and_(MovNota.empresa==foreign(MovNotaItem.empresa), "
                    "MovNota.numerodocumento==foreign(MovNotaItem.numerodocumento))"
    )


class MovNotaItem(Base):
    __tablename__ = "movnotaitem"

    empresa = Column(Integer, primary_key=True)
    numerodocumento = Column(Integer, primary_key=True)
    codigovendedor = Column(String(6), primary_key=True)
    codigoproduto = Column(String(6), primary_key=True)
    idpedido = Column(Integer, primary_key=True)
    descricaoproduto = Column(String(255))
    valorUnitario = Column(Float, default=0.0)
    valorunitariovenda = Column(Float, default=0.0)
    valorDesconto = Column(Float, default=0.0)
    valorTotal = Column(Float, default=0.0)
    quantidade = Column(Float, default=0.0)
    dataRegistro = Column(DateTime)
    codigocliente = Column(String(6))
    valoracrescimo = Column(Float, default=0.0)
    situacaoRegistro = Column(String(1), default='I')

    pedido = relationship(
        "MovNota",
        back_populates="itens",
        primaryjoin="and_(foreign(MovNotaItem.empresa)==MovNota.empresa, "
                    "foreign(MovNotaItem.numerodocumento)==MovNota.numerodocumento)"
    )
