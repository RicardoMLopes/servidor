# cadformapagamento_schema.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Schema para leitura (response)
class FormaPagamentoSchema(BaseModel):
    id: int
    empresa: int
    codigo: str
    descricao: Optional[str] = None
    acrescimo: float
    desconto: float
    situacaoRegistro: str
    dataRegistro: Optional[datetime] = None

    class Config:
        from_attributes = True  # substitui orm_mode no Pydantic v2

# Schema para criação/atualização (request)
class FormaPagamentoCreateSchema(BaseModel):
    empresa: int
    codigo: str
    descricao: Optional[str] = None
    acrescimo: float = 0.0
    desconto: float = 0.0
    situacaoRegistro: str = "I"
    dataRegistro: Optional[datetime] = None
