from pydantic import BaseModel, condecimal, field_validator, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal

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
    limiteCredito: Optional[Decimal] = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)
    observacao: Optional[str] = None
    restricao: Optional[str] = None
    reajuste: Optional[Decimal] = Field(default=Decimal("0.00"), max_digits=5, decimal_places=2)
    situacaoRegistro: Optional[str] = "A"
    dataRegistro: Optional[datetime] = None
    versao: Optional[int] = 1

    # Validador para converter string vazia ou nula em None no campo de data
    @field_validator('dataRegistro', mode='before')
    def validar_data(cls, value):
        if value == "" or value is None:
            return None
        return value

    # Validador para garantir que valores numéricos/decimais não quebrem se vierem vazios
    @field_validator('limiteCredito', 'reajuste', mode='before')
    def validar_decimais(cls, value):
        if value == "" or value is None:
            return Decimal("0.00")
        return value

    class Config:
        from_attributes = True # ⚠️ Pydantic v2

# Agora define ClienteCreate
class ClienteCreate(ClienteBase):
    pass

# Outras classes
class ClienteOutComId(ClienteBase):
    id: int

class ClienteOutSemId(ClienteBase):
    pass
