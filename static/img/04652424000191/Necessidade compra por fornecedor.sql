SELECT A.Aplicacao, A.Codigo,A.codigobarra, A.Descricao,A.SaldoEstoque,A.unidade,A.precocusto,
       CASE 
          WHEN B.Movimentacao = 'E'
             THEN 
                B.Quantidade 
             END AS Compras,
       CASE 
          WHEN B.Movimentacao = 'E'
             THEN 
               B.ValorUnitario 
             END As ValorCampra,
       CASE 
          WHEN B.Movimentacao = 'E'
             THEN 
               (B.Quantidade * ValorUnitario) 
             END As TotalCompras,                

       CASE 
          WHEN B.Movimentacao = 'S'
             THEN 
                B.Quantidade
             END As Vendas,  
       CASE 
          WHEN B.Movimentacao = 'S'
             THEN 
                B.ValorUnitario
             END As ValorVenda,
       CASE 
          WHEN B.Movimentacao = 'S'
             THEN 
                (B.Quantidade * ValorUnitario)
             END As TotalVenda,
       CASE 
          WHEN B.Movimentacao = 'S'
             THEN 
                B.ValorCusto 
             END As CustoVenda,
       CASE 
          WHEN B.Movimentacao = 'S'
             THEN 
                (B.Quantidade * B.ValorCusto) 
             END As TotalCusto,
       CASE 
          WHEN B.Movimentacao = 'S'
             THEN 
                ((B.Quantidade * ValorUnitario) - (B.Quantidade * 
B.ValorCusto)) 
             END As LocroVenda             
   FROM CadProduto A 
      INNER JOIN movnotaItem B ON
         A.Empresa = B.Empresa AND 
         A.Codigo = B.CodigoProduto 
      INNER JOIN movnota C ON
         B.Empresa = C.Empresa AND
         B.NomeComputador = C.NomeComputador AND
         B.Movimentacao = C.Movimentacao AND
         B.Procedimento = C.Procedimento AND
         B.CodigoFornecCliente = C.CodigoFornecCliente 
where A.Aplicacao = ?[S]Aplicacao AND
      B.Procedimento NOT IN ('O', 'I', 'P') AND
      C.DataEmissao BETWEEN ?[T]Data_Inicial AND ?[T]Data_Final 
Group By A.Aplicacao, A.Codigo, A.Descricao, B.Movimentacao
