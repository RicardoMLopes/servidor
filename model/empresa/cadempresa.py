# cadempresa_model.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

empresa_Base = declarative_base()

class CadEmpresa(empresa_Base):
    __tablename__ = "cadempresa"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    codigo = Column(String(255), nullable=True, index=True)
    nome = Column(String(255), nullable=True)
    cnpj = Column(String(255), nullable=True)
    rua = Column(String(255), nullable=True)
    numero = Column(String(255), nullable=True)
    bairro = Column(String(255), nullable=True)
    cidade = Column(String(255), nullable=True)
    telefone = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
