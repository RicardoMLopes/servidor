SELECT A.CodigoProduto, C.Descricao, Sum(A.Quantidade) AS QTD FROM MovNotaItem A
INNER JOIN MovNota B ON
A.Movimentacao = B.Movimentacao AND
A.Procedimento = B.Procedimento AND
A.NumeroDocumento = B.NumeroDocumento AND
A.CodigoFornecCliente = B.CodigoFornecCliente
INNER JOIN CadProduto C ON
C.Codigo = A.CodigoProduto 
WHERE A.Movimentacao = 'S' AND
A.Procedimento = 'O'
Group By CodigoProduto, Descricao