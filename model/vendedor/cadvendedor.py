from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, BigInteger
from sqlalchemy.orm import declarative_base

v_Base = declarative_base()

class CadVendedor(v_Base):
    __tablename__ = "cadvendedor"

    id = Column(Integer, primary_key=True, autoincrement=True)  # id incremental
    empresa = Column(Integer, nullable=False)
    codigo = Column(String(6), nullable=False)
    cd_rota = Column(DECIMAL(10,0), nullable=True)
    nome = Column(String(80), nullable=False)
    situacaoRegistro = Column(String(1), default="I")
    dataRegistro = Column(DateTime, nullable=True)