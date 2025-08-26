from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# -------------------------------
# Modelos SQLAlchemy
# -------------------------------

class MovNota(Base):
    __tablename__ = "movnota"

    id = Column(Integer, primary_key=True, autoincrement=True)
    empresa = Column(Integer, nullable=False)
    numerodocumento = Column(Integer, nullable=False)
    codigovendedor = Column(String(5), nullable=False)
    codigocliente = Column(String(5), nullable=False)
    codigocondPagamento = Column(String(5), nullable=False)
    nomecliente = Column(String(100))
    idpedido = Column(Integer)
    valorDesconto = Column(Numeric(12,2), default=0)
    valorDespesas = Column(Numeric(12,2), default=0)
    valorFrete = Column(Numeric(12,2), default=0)
    valorTotal = Column(Numeric(12,2), nullable=False, default=0)
    pesoTotal = Column(Numeric(12,2), default=0)
    observacao = Column(Text)
    status = Column(String(1), default='P')  # P=pendente, R=recebido
    dataLancamento = Column(DateTime)
    dataRegistro = Column(DateTime, default=func.now())
    situacaoRegistro = Column(String(1), default='I')
    pedido_hash = Column(String(64), unique=True)

    itens = relationship(
        "MovNotaItem",
        back_populates="pedido",
        cascade="all, delete-orphan"
    )


class MovNotaItem(Base):
    __tablename__ = "movnotaitem"

    id = Column(Integer, primary_key=True, autoincrement=True)
    movnota_id = Column(Integer, ForeignKey("movnota.id"), nullable=False)
    empresa = Column(Integer, nullable=False)
    numerodocumento = Column(Integer, nullable=False)
    codigovendedor = Column(String(5), nullable=False)
    codigoproduto = Column(String(5), nullable=False)
    idpedido = Column(Integer)
    descricaoproduto = Column(String(200))
    quantidade = Column(Numeric(12,6), default=0)
    valorUnitario = Column(Numeric(12,6), default=0)
    valorunitariovenda = Column(Numeric(12,6), default=0)
    valorDesconto = Column(Numeric(12,2), default=0)
    valoracrescimo = Column(Numeric(12,2), default=0)
    valorTotal = Column(Numeric(12,2), default=0)
    codigocliente = Column(String(5))
    situacaoRegistro = Column(String(1), default='I')
    dataRegistro = Column(DateTime, default=func.now())

    pedido = relationship(
        "MovNota",
        back_populates="itens"
    )



# -------------------------------
# Dicionários de colunas (verificação)
# -------------------------------
# pedido.py

# -------------------------------
# Estrutura das colunas e PKs
# -------------------------------

colunas_movnota = {
    "id": "INT AUTO_INCREMENT",
    "empresa": "INT NOT NULL",
    "numerodocumento": "INT NOT NULL",
    "codigovendedor": "CHAR(5) NOT NULL",
    "codigocliente": "CHAR(5) NOT NULL",
    "codigocondPagamento": "CHAR(5) NOT NULL",
    "nomecliente": "VARCHAR(100) DEFAULT NULL",
    "idpedido": "INT DEFAULT NULL",
    "valorDesconto": "DECIMAL(12,2) DEFAULT '0.00'",
    "valorDespesas": "DECIMAL(12,2) DEFAULT '0.00'",
    "valorFrete": "DECIMAL(12,2) DEFAULT '0.00'",
    "valorTotal": "DECIMAL(12,2) DEFAULT '0.00'",
    "pesoTotal": "DECIMAL(12,2) DEFAULT '0.00'",
    "observacao": "TEXT",
    "status": "CHAR(1) DEFAULT 'P'",
    "dataLancamento": "DATETIME DEFAULT NULL",
    "dataRegistro": "DATETIME DEFAULT NULL",
    "situacaoRegistro": "VARCHAR(1) DEFAULT 'I'",
    "pedido_hash": "CHAR(64) DEFAULT NULL"
}

pks_movnota = [
    "id", "empresa", "numerodocumento",
    "codigovendedor", "codigocliente", "codigocondPagamento"
]

colunas_movnotaitem = {
    "id": "INT AUTO_INCREMENT",
    "movnota_id": "INT NOT NULL",
    "empresa": "INT NOT NULL",
    "numerodocumento": "INT NOT NULL",
    "codigovendedor": "CHAR(5) NOT NULL",
    "codigoproduto": "CHAR(5) NOT NULL",
    "idpedido": "INT DEFAULT NULL",
    "descricaoproduto": "VARCHAR(200) DEFAULT NULL",
    "quantidade": "DECIMAL(12,6) DEFAULT 0.000000",
    "valorUnitario": "DECIMAL(12,6) DEFAULT 0.000000",
    "valorunitariovenda": "DECIMAL(12,6) DEFAULT 0.000000",
    "valorDesconto": "DECIMAL(12,2) DEFAULT 0.00",
    "valoracrescimo": "DECIMAL(12,2) DEFAULT 0.00",
    "valorTotal": "DECIMAL(12,2) DEFAULT 0.00",
    "codigocliente": "CHAR(5) DEFAULT NULL",
    "situacaoRegistro": "VARCHAR(1) DEFAULT 'I'",
    "dataRegistro": "DATETIME DEFAULT NULL"
}



pks_movnotaitem = [
    "id", "movnota_id", "empresa",
    "numerodocumento", "codigovendedor", "codigoproduto"
]

# -------------------------------
# Exportações do módulo
# -------------------------------

__all__ = [
    "colunas_movnota",
    "colunas_movnotaitem",
    "pks_movnota",
    "pks_movnotaitem"
]
