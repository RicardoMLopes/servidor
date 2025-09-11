# cadvendedor_schema.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Schema para leitura (response)
class VendedorSchema(BaseModel):
    id: int
    empresa: int
    codigo: str
    cd_rota: Optional[float] = None
    nome: str
    situacaoRegistro: str
    dataRegistro: Optional[datetime] = None
    versao: int

    class Config:
        from_attributes = True  # substitui orm_mode no Pydantic v2

# Schema para criação/atualização (request)
class VendedorCreateSchema(BaseModel):
    empresa: int
    codigo: str
    cd_rota: Optional[float] = None
    nome: str
    situacaoRegistro: str = "I"
    dataRegistro: Optional[datetime] = None
    versao: int
