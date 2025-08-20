SELECT A.CodigoProduto, C.Descricao, SUM(Quantidade) AS Quantidade, 
	AVG(ValorUnitario) AS ValorUnitario, SUM(ValorTotal) As ValorTotal
	FROM MovNotaItem A
		INNER JOIN MovNota B ON
			B.Empresa = A.Empresa AND
			B.Movimentacao = A.Movimentacao AND
			B.Procedimento = A.Procedimento AND
			B.NumeroDocumento = A.NumeroDocumento AND
			B.CodigoFornecCliente = A.CodigoFornecCliente
		INNER JOIN CadProduto C ON
			C.Empresa = A.Empresa AND
			C.Codigo = A.CodigoProduto AND
			C.Servico = 'S'
	WHERE A.Empresa = '00001' AND 
		A.Movimentacao = 'S' AND 
		B.DataLancamento BETWEEN :[D]Data_Inicial AND :[D]Data_Final 
	GROUP BY A.CodigoProduto, C.Descricao