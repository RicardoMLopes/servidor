from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Schema para leitura (response)
class ParametroSchema(BaseModel):
    empresa: int
    vendedorPadrao: Optional[str] = None
    controlaSaldoEstoque: bool
    casaDecimalQuantidade: int
    casaDecimalValor: int
    percentualDescontoVenda: float
    datacatalogo: Optional[datetime] = None
    situacaoRegistro: str
    dataRegistro: datetime

    class Config:
        from_attributes = True  # substitui orm_mode no Pydantic v2


# Schema para criação/atualização (request)
class ParametroCreateSchema(BaseModel):
    empresa: int
    vendedorPadrao: Optional[str] = None
    controlaSaldoEstoque: bool = True
    casaDecimalQuantidade: int = 0
    casaDecimalValor: int = 2
    percentualDescontoVenda: float = 0.0
    datacatalogo: Optional[datetime] = None
    situacaoRegistro: str = "I"
    dataRegistro: datetime
