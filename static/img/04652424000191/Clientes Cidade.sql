select codigo, nome, nomefantasia, endereco, bairro, telefone, cidade 
from cadcliente
 where cidade like ?[S]NomeCidade
  Order By Bairro, Nome