from pydantic import BaseModel, constr, condecimal
from typing import Optional

class ClienteCreate(BaseModel):
    empresa: str
    codigo: str
    codigovendedor: str
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
    dataRegistro: Optional[str] = None  # pode ser datetime se quiser
    versao: Optional[str] = "1.0"
