Select B.Nome, A.PercentualComissao, 
	SUM(A.ValorTotal) AS ValorVenda, 
	SUM(A.ValorTotal*A.PercentualComissao/100) AS ValorComissao
	from MovNotaItem A 
		INNER JOIN movnota X ON
			X.Empresa = A.Empresa AND
			X.NomeComputador = A.NomeComputador AND
			X.NumeroDocumento = A.NumeroDocumento AND
			X.Serie = A.Serie AND
			X.Modelo = A.Modelo AND
			X.CodigoFornecCliente = A.CodigoFornecCliente
		INNER JOIN cadfuncionario B ON
			B.Empresa = A.Empresa AND
			B.Codigo = A.CodigoVendedor
	where A.Empresa = ?[C5]Empresa AND
		X.DataLancamento BETWEEN ?[D]Data_Inicial AND ?[D]Data_Final AND
		A.Procedimento = 'L' AND
		A.Movimentacao = 'S' AND
		A.SituacaoRegistro <> 'E'
	GROUP BY B.Nome, A.PercentualComissao