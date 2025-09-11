from pydantic import BaseModel, condecimal
from typing import Optional
from datetime import datetime

# Base que todas herdam
class ClienteBase(BaseModel):
    empresa: str
    codigo: str
    codigovendedor: Optional[str] = None
    nome: str
    contato: Optional[str] = None
    cpfCnpj: Optional[str] = None
    rua: Optional[str] = None
    numero: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    telefone: Optional[str] = None
    limiteCredito: Optional[condecimal(max_digits=12, decimal_places=2)] = 0
    observacao: Optional[str] = None
    restricao: Optional[str] = None
    reajuste: Optional[condecimal(max_digits=5, decimal_places=2)] = 0
    situacaoRegistro: Optional[str] = "A"
    dataRegistro: Optional[datetime] = None
    versao: Optional[int] = 1

    class Config:
        from_attributes = True  # ⚠️ Pydantic v2

# Agora define ClienteCreate
class ClienteCreate(ClienteBase):
    pass

# Outras classes
class ClienteOutComId(ClienteBase):
    id: int

class ClienteOutSemId(ClienteBase):
    pass
