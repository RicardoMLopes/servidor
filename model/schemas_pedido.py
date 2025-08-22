from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

class ItemSchema(BaseModel):
    tipo: str = "MovNotaItem"   # Identificador fixo
    codigoproduto: str
    descricaoproduto: Optional[str]
    quantidade: Decimal
    valorUnitario: Decimal
    valorunitariovenda: Decimal
    valorDesconto: Decimal
    valorTotal: Decimal
    valoracrescimo: Decimal

    class Config:
        orm_mode = True
        json_encoders = {Decimal: float, datetime: str}

class PedidoSchema(BaseModel):
    tipo: str = "MovNota"       # Identificador fixo
    empresa: int
    numerodocumento: int
    codigovendedor: str
    codigocliente: str
    nomecliente: Optional[str]
    idpedido: Optional[int]
    valorDesconto: Decimal
    valorDespesas: Decimal
    valorFrete: Decimal
    valorTotal: Decimal
    pesoTotal: Decimal
    observacao: Optional[str]
    status: Optional[str]
    dataLancamento: Optional[datetime]
    dataRegistro: Optional[datetime]
    situacaoRegistro: Optional[str]
    itens: List[ItemSchema] = []

    class Config:
        orm_mode = True
        json_encoders = {Decimal: float, datetime: str}
