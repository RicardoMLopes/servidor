   SELECT B.CodigoProduto, B.LocalEstoque, B.CST AS CSTProduto, 
       	B.CFOP As CFOPProduto, 
       	B.Quantidade AS A3Quantidade, B.ValorDesconto AS A2ValorDescontoProduto, 
       	B.ICMS AS A1ICMSProduto, B.PercentualReducaoBCICMS AS A2PRBICMSProduto, B.IPI As A1IPIProduto,
       	B.ValorUnitario AS A2ValorUnitario, B.Aliquota AS A2Aliquota,
       	B.ValorCusto AS A2ValorCusto, 	B.ValorTotal AS A2ValorTotal,
       	B.SituacaoTributaria, 
       SUBSTRING(IFNULL(CONCAT(D.Descricao),D.Descricao) FROM 1
FOR 240) AS NomeProduto, D.Unidade
       FROM MovNota A
          	LEFT JOIN MovNotaItem B ON
             		B.Empresa = A.Empresa AND             
			B.NumeroDocumento = A.NumeroDocumento AND             
			B.Movimentacao = A.Movimentacao AND             
			B.Procedimento = A.Procedimento AND             
			B.IndiceNumeroNF = A.IndiceNumeroNF AND
			B.CodigoFornecCliente = A.CodigoFornecCliente          
		INNER JOIN CadProduto D ON             
			D.Empresa = A.Empresa AND             	
			D.Codigo = B.CodigoProduto AND	     
			D.Servico = 'N' 
	[:FILTRO]