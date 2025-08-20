SELECT DISTINCT B.ICMS As A2AliquotaISSServico
       FROM MovNota A
          INNER JOIN MovNotaItem B ON
             B.Empresa = A.Empresa AND
             B.NumeroDocumento = A.NumeroDocumento AND
             B.Movimentacao = A.Movimentacao AND
             B.Procedimento = A.Procedimento AND
             B.CodigoFornecCliente = A.CodigoFornecCliente
          INNER JOIN CadCliente C ON
             C.Empresa = A.Empresa AND
             C.Codigo = A.CodigoFornecCliente
          INNER JOIN CadProduto D ON
             D.Empresa = A.Empresa AND
             D.Codigo = B.CodigoProduto AND
	     D.Servico = 'S'
