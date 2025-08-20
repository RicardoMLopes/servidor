SELECT C.Aplicacao,  A.Vendedor, D.Nome, B.CodigoProduto, C.Descricao, SUM(B.ValorTotal) As Valor
	FROM MovNota A
		INNER JOIN MovNotaItem B ON
			B.Empresa = A.Empresa AND
			B.Movimentacao = A.Movimentacao AND
			B.Procedimento = A.Procedimento AND
			B.NumeroDocumento = A.NumeroDocumento AND
			B.CodigoFornecCliente = A.CodigoFornecCliente
		INNER JOIN CadProduto C ON
			C.Empresa = B.Empresa AND
			C.Codigo = B.CodigoProduto
		INNER JOIN CadFuncionario D ON
			D.Empresa = A.Empresa AND
			D.Codigo = A.Vendedor
	WHERE A.Empresa = '00001' AND
		A.Movimentacao = 'S' AND
		A.Procedimento = 'L' AND
		A.DataLancamento BETWEEN ?[D]Data_Inicial AND ?[D]Data_Final 
	GROUP BY C.Aplicacao,  A.Vendedor, B.CodigoProduto, C.Descricao, D.Nome

