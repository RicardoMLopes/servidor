# cadvendedor_schema.py
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional

# Schema para leitura (response)
class VendedorSchema(BaseModel):  # <--- Altere o nome da classe para VendedorSchema
    empresa: int
    codigo: str = Field(..., max_length=6)
    nome: str = Field(..., max_length=80)
    cd_rota: Optional[float] = None
    situacaoRegistro: Optional[str] = "I"
    dataRegistro: Optional[datetime] = None
    limitedesconto: Optional[float] = 0.0
    versao: Optional[int] = 1

    @field_validator("empresa", mode="before")
    def parse_empresa(cls, v):
        if isinstance(v, str):
            return int(v.strip())
        return v

    class Config:
        from_attributes = True

# Schema para criação/atualização (request)
class VendedorCreateSchema(BaseModel):
    empresa: int
    codigo: str
    cd_rota: Optional[float] = None
    nome: str
    situacaoRegistro: str = "I"
    dataRegistro: Optional[datetime] = None
    versao: int
