SELECT CodigoProduto, SUM(A.Quantidade) As QuantidadeAtendida
	FROM MovNotaItem A
	WHERE Empresa = '00001' AND
		Movimentacao = 'S' AND
		Procedimento = 'L'
	GROUP BY CodigoProduto