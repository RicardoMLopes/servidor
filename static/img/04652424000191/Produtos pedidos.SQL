SELECT CodigoProduto, C.Descricao, C.PesoProduto, C.SaldoEstoque, 
	SUM(A.Quantidade) As QuantidadePedida
	FROM MovNotaItem A
		INNER JOIN CadProduto C ON
			C.Empresa = A.Empresa AND
			C.Codigo = A.CodigoProduto
	WHERE Empresa = '00001' AND
		Movimentacao = 'S' AND
		Procedimento = 'R'
	GROUP BY CodigoProduto, C.Descricao, C.PesoProduto, C.SaldoEstoque