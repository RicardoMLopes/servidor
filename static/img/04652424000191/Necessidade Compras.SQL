SELECT A.CodigoProduto, C.CodigoBarra, C.Descricao, C.SaldoEstoque, 
	SUM(A.Quantidade) AS Orcamento, 
	C.SaldoEstoque-SUM(A.Quantidade) As Necessidade
	FROM MovNotaItem A
		INNER JOIN MovNota B ON
			B.Empresa = A.Empresa AND
			B.NomeComputador = A.NomeComputador AND
			B.NumeroDocumento = A.NumeroDocumento AND
			B.Procedimento = A.Procedimento AND
			B.Movimentacao = A.Movimentacao AND
			B.CodigoFornecCliente = A.CodigoFornecCliente AND
			B.Serie = A.Serie AND
			B.Modelo = A.Modelo AND
			B.IndiceNumeroNF = A.IndiceNumeroNF
		INNER JOIN CadProduto C ON
			C.Empresa = A.Empresa AND
			C.Codigo = A.CodigoProduto
	WHERE A.Empresa = '00001'
		AND A.Procedimento = 'O'
		AND A.Movimentacao = 'S'
		AND B.DataEmissao BETWEEN ?[D]Data_Inicial AND ?[D]Data_Final  
	GROUP BY A.CodigoProduto, C.Descricao, C.SaldoEstoque
	HAVING C.SaldoEstoque < SUM(A.Quantidade)
