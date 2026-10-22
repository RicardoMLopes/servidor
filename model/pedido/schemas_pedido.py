from pydantic import BaseModel, constr, condecimal
from typing import List, Optional
from decimal import Decimal
from datetime import date, datetime

class ItemSchema(BaseModel):
    tipo: constr(max_length=20) = "MovNotaItem"  # Identificador fixo
    tipodocumento: constr(max_length=10) = "PEDIDO"
    codigoproduto: constr(max_length=5)
    idpedido: Optional[int] = None
    descricaoproduto: Optional[constr(max_length=200)] = None
    quantidade: condecimal(max_digits=12, decimal_places=6)
    quantidade_pedida: condecimal(max_digits=12, decimal_places=6) = 0
    valorUnitario: condecimal(max_digits=12, decimal_places=6)
    valorunitariovenda: condecimal(max_digits=12, decimal_places=6)
    valorDesconto: condecimal(max_digits=12, decimal_places=2) = 0
    valoracrescimo: condecimal(max_digits=12, decimal_places=2) = 0
    valorTotal: condecimal(max_digits=12, decimal_places=2)
    situacaoRegistro: Optional[constr(max_length=1)] = "I"
    dataRegistro: Optional[datetime] = None

    # 🔹 Novos campos do modal
    data_pedido_previsto: Optional[date] = None
    ordem_compra: Optional[constr(max_length=50)] = None
    item_ordem_compra: Optional[constr(max_length=20)] = None
    material: Optional[constr(max_length=100)] = None
    referencia: Optional[constr(max_length=100)] = None

    class Config:
        from_attributes = True  # substitui orm_mode no Pydantic v2
        json_encoders = {Decimal: float, datetime: str, date: str}

class PedidoSchema(BaseModel):
    tipo: constr(max_length=20) = "MovNota"  # Identificador fixo
    empresa: int
    numerodocumento: int
    codigovendedor: constr(max_length=5)
    codigocliente: constr(max_length=5)
    codigocondPagamento: constr(max_length=5)
    nomecliente: Optional[constr(max_length=100)] = None
    idpedido: Optional[int] = None
    valorDesconto: condecimal(max_digits=12, decimal_places=2) = 0
    valorDespesas: condecimal(max_digits=12, decimal_places=2) = 0
    valorFrete: condecimal(max_digits=12, decimal_places=2) = 0
    valorTotal: condecimal(max_digits=12, decimal_places=2) = 0
    pesoTotal: condecimal(max_digits=12, decimal_places=2) = 0
    observacao: Optional[constr(max_length=255)] = None
    status: Optional[constr(max_length=1)] = "P"
    dataLancamento: Optional[datetime] = None
    dataRegistro: Optional[datetime] = None
    situacaoRegistro: Optional[constr(max_length=1)] = "I"
    itens: List[ItemSchema] = []
    pedido_hash: Optional[constr(max_length=64)] = None  # idempotência

    class Config:
        orm_mode = True
        json_encoders = {Decimal: float, datetime: str}

