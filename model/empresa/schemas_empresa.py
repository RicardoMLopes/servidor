from pydantic import BaseModel
from typing import Optional

# Schema de leitura (response)
class EmpresaSchema(BaseModel):
    id: int
    codigo: Optional[str] = None
    nome: Optional[str] = None
    cnpj: Optional[str] = None
    rua: Optional[str] = None
    numero: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True  # substitui orm_mode no Pydantic v2


# Schema de criação/atualização (request)
class EmpresaCreateSchema(BaseModel):
    codigo: Optional[str] = None
    nome: Optional[str] = None
    cnpj: Optional[str] = None
    rua: Optional[str] = None
    numero: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
