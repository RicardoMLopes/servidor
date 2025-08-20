SELECT Parcela As A0NumeroFin2
	FROM MovNota A
		INNER JOIN MovFinanceiro B On
			B.Empresa = A.Empresa AND
			B.NumeroDocumento = '0000'+A.NumeroDocumento AND
			B.CodigoFornecedorCliente = A.CodigoFornecCliente AND
			B.Movimentacao = A.Movimentacao AND
			B.Parcela = 2 

			
		