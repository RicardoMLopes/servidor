from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Boolean, Float
from sqlalchemy.orm import declarative_base

param_Base = declarative_base()

from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Boolean
from sqlalchemy.orm import declarative_base

param_Base = declarative_base()

class CadParametro(param_Base):
    __tablename__ = "cadparametro"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    empresa = Column(Integer, primary_key=True, index=True)

    vendedorPadrao = Column(String(6), nullable=True)

    controlaSaldoEstoque = Column(Boolean, nullable=False, default=True)
    casaDecimalQuantidade = Column(Integer, nullable=False, default=0)
    casaDecimalValor = Column(Integer, nullable=False, default=2)

    percentualDescontoVenda = Column(DECIMAL(15, 6), nullable=False, default=0)

    datacatalogo = Column(DateTime, nullable=True)
    situacaoRegistro = Column(String(1), nullable=False, default="I")
    dataRegistro = Column(DateTime, nullable=False)
