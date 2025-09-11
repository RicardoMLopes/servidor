from pydantic import BaseModel, condecimal
from typing import Optional
from datetime import datetime

class ProdutoBase(BaseModel):
    empresa: int
    codigo: str
    descricao: str
    unidadeMedida: Optional[str] = None
    codigoBarra: Optional[str] = None
    agrupamento: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    tamanho: Optional[str] = None
    cor: Optional[str] = None
    peso: Optional[condecimal(max_digits=15, decimal_places=6)] = 0
    precoVenda: Optional[condecimal(max_digits=15, decimal_places=6)] = 0
    percentualDesconto: Optional[condecimal(max_digits=15, decimal_places=6)] = 0
    estoque: Optional[condecimal(max_digits=15, decimal_places=6)] = 0
    reajustaCondicaoPagamento: Optional[str] = "N"
    percentualComissao: Optional[condecimal(max_digits=15, decimal_places=6)] = 0
    situacaoRegistro: Optional[str] = "I"
    dataRegistro: Optional[datetime] = None
    versao: Optional[int] = 1
    imagens: Optional[bool] = False

    class Config:
        from_attributes = True  # ⚠️ Pydantic v2

# Para criar produto
class ProdutoCreate(ProdutoBase):
    pass

# Output completo (exemplo com id fictício, se precisar)
class ProdutoOutComId(ProdutoBase):
    id: Optional[int]  # apenas se tiver id interno separado

# Output sem id
class ProdutoOutSemId(ProdutoBase):
    pass
