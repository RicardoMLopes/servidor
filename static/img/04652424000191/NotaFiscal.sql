   SELECT A.NumeroDocumento,'LANCAMENTO:' AS TipoMovimentacao, A.Movimentacao,'SIA - Sistema Integrado Administrativo' AS Titulo1, 'Nao e valido como comprovante fiscal!' AS titulo2,'--------------------------------------------------------------------------------------------------------------------------------------'AS titulo3,'--------------------------------------------------------------------------------------------------------------------------------------'AS titulo4,'Codigo Produto/Servico' AS DescProduto,'UN' AS DescUnidade,'Quant' As DescQuantidade,'Desc' As Desconto2,'ICMS%' AS DescICMS,'IPI%' AS DescIPI,'Vr.unit' As DescValorUnit,'Vr.Total' AS DescValorTotal,'Frete' AS DescFrete,'Desp/Ser.:'AS DescDespesa,'Desc.:' AS TotalDesc,'ICMS:' AS 1DescICMS,'IPI:' AS 1DescIPI,'Total Nota:' AS DescTotal,' Assinatura:__________________________________________________________' AS Assinatura,     
       	A.CodigoFornecCliente, A.Serie, A.Modelo,'Data de Emissao:' AS DescEmissao, A.DataEmissao,'Data de Lancamento:' AS DescLancamento,A.Datalancamento,'Cond. Pagamento:' AS DescCondPagamento,'Total Documento:' AS DescTotalDocumento,
	A.CodigoCondicaoPagamento, A.ResponsavelFrete, A.Transportadora,'Obsevarcao:'DescObsevarcao,
       	A.ValorFrete 	AS A2ValorFrete, A.Placa, A.AliquotaICMSFrete AS A2AliquotaICMSFrete, 
       	A.ValorICMSFrete AS A2ValorICMSFrete, A.ValorDespesas AS A2ValorDespesas, 
       	'Valor de desconto da Nota:' As TituloDesconto, A.ValorDesconto AS A2ValorDesconto,
       	A.Vendedor,'Vendedor:' AS DescVendedor, A.ValorTotal AS A2ValorTotal,      
        A.BaseCalculoICMS As 	A2BaseCalculoICMS, A.AliquotaICMS AS A2AliquotaICMS, A.ValorICMS AS A2ValorICMS, 
       	A.ValorIPI AS A2ValorIPI, A.ValorDocumento AS A2ValorDocumento,
       	A.ValorDocumento As EXTENSO001,
       	A.ValorDocumento As EXTENSO041,
       	A.ValorDocumento As EXTENSO081,
	CASE WHEN A.CodigoFornecCliente = '00003' 
		THEN 'Classificacao Fiscal: 94.01.90.90'	
		ELSE 'Classificacao Fiscal: 87.08.29.99' END AS ClassificacaoFiscal, 
	'PIS 0,1% = ' AS TituloPIS, (A.ValorDocumento+A.ValorDesconto)*0.001 AS A2ValorPIS,
	' - COFINS 0,5% = ' AS TituloCOFINS, (A.ValorDocumento+A.ValorDesconto)*0.005 AS A2ValorCOFINS,
	' - Imposto retido conforme lei 11.196 de 22/11/2005' AS DescricaoLeiPIS, 
       	A.CFOP, A.BaseCalculoICMSSubstituic AS 	A2BaseCalculoICMSSubstitu, 
	A.ValorICMSSubstituicao AS 	A2ValorICMSSubstituicao, 
	A.ValorICMSComplementar AS 	A2ValorICMSComplementar,
       	A.ValorSeguro AS A2ValorSeguro, A.ValorIsencao AS 	A2ValorIsensao, 
       	'' AS CodigoProduto, '' AS NumeroPedido, '' AS LocalEstoque, '' AS CSTProduto, 
       	'' As CFOPProduto, 
       	0 AS A3Quantidade, 0 AS A2ValorDescontoProduto, 
       	0 AS A1ICMSProduto, 0 AS A2PRBICMSProduto, 0 As A1IPIProduto,
       	0 AS A2ValorUnitario, 0 AS A2Aliquota,
       	0 AS A2ValorCusto, 0 AS A2ValorTotal,
       	'' AS SituacaoTributaria, 
       	CONCAT(A.CodigoFornecCliente,'-',CASE WHEN Movimentacao = 'S' THEN C.Nome ELSE G.Nome END) AS NomeCliente,'Cliente:' AS DescNome, 
	CASE WHEN Movimentacao = 'S' THEN C.Endereco ELSE G.Endereco END AS Endereco,'Endereco:' AS DescEndereco, 
	CASE WHEN Movimentacao = 'S' THEN C.Bairro ELSE G.Bairro END AS Bairro,'Bairro:' AS DescBairro, 
	CASE WHEN Movimentacao = 'S' THEN C.Cidade ELSE G.Cidade END As Cidade,'Cidade:' AS DescCidade, 
       	CASE WHEN Movimentacao = 'S' THEN C.Telefone ELSE G.Telefone END AS Telefone,'Telefone:' AS DescTelefone, 
	CASE WHEN Movimentacao = 'S' THEN C.CNPJCPF ELSE G.CNPJCPF END AS CNPJCPF,'CNPJ/CPF:' AS DescCNPJCPF,
        CASE WHEN Movimentacao = 'S' THEN H.Nome ELSE H.Nome END As NomeVendedor, 
        CASE WHEN Movimentacao = 'S' THEN I.Nome ELSE I.Nome END As NomeCondpagamento, 
	CASE WHEN Movimentacao = 'S' THEN C.InscricaoEstadual ELSE G.InscricaoEstadual END AS InscricaoEstadual,'RG/Insc:' AS DescInscEstadual, 
	CASE WHEN Movimentacao = 'S' THEN C.UF ELSE G.UF END As UF, 
	CASE WHEN Movimentacao = 'S' THEN C.CEP ELSE G.CEP END AS CEP,'CEP' AS DescCEP,
       	'' AS NomeProduto, '' AS Unidade,
       	E.Descricao AS DescicaoCFOP, 
       	F.Nome AS NomeTransportadora, F.CnpjCpf AS CNPJTransporte,
       	F.UF AS UFTransportadora, F.Endereco AS EndTransportadora,
       	F.Cidade AS CidTransportadora, F.InscricaoEstadual AS InsEstTransportadora,	 
	SUBSTRING(A.Observacao FROM 1 FOR 58) As Observacao,       
	SUBSTRING(A.Observacao 	FROM 59 FOR 58) As Observacao1,
       	SUBSTRING(A.Observacao FROM 118 FOR 58) As Observacao2,
       	SUBSTRING(A.Observacao FROM 177 FOR 38) As Observacao3,
       	SUBSTRING(A.Observacao FROM 216 FOR 38) As Observacao4,
       	SUBSTRING(A.Observacao1 FROM 1 FOR 38) As Observacao5,
       	SUBSTRING(A.Observacao1 FROM 39 FOR 58) As Observacao6,
       	SUBSTRING(A.Observacao1 FROM 98 FOR 58) As Observacao7,
       	SUBSTRING(A.Observacao1 FROM 157 FOR 58) As Observacao8,
       	SUBSTRING(A.Observacao1 FROM 216 FOR 58) As Observacao9,
	0 AS A2ValorTotalProdutos, 0 AS A0NumeroFin1, 0 AS A0NumeroFin2, 0 AS A0NumeroFin3,
       	'' AS DataVencimentoFin1, '' AS DataVencimentoFin2, '' AS DataVencimentoFin3,
       	0 AS A2ValorFin1, 0 AS A2ValorFin2, 0 AS A2ValorFin3,
       	'' AS NomeServico, '' AS UnidadeServico, 0 AS A2QtdServico, 0 AS A2ValorServico,
       	0 AS A2ValorTotalServico, A.FretePesoBruto AS A2FretePesoBruto, 
	A.FretePesoLiquido AS A2FretePesoLiquido
       FROM MovNota A
		LEFT JOIN CadCliente C ON             
			C.Empresa = A.Empresa AND             
			C.Codigo = A.CodigoFornecCliente          
		LEFT JOIN CadCFOP E ON             
			E.Empresa = A.Empresa AND             
			E.Codigo = A.CFOP          
		LEFT JOIN CadFornecedor F ON             
			F.Empresa = A.Empresa AND             
			F.Codigo = A.Transportadora 
		LEFT JOIN CadFornecedor G ON             
			G.Empresa = A.Empresa AND             
			G.Codigo = A.CodigoFornecCliente 
                LEFT JOIN CadFuncionario H ON             
			H.Empresa = A.Empresa AND             
			H.Codigo = A.Vendedor         
                LEFT JOIN CadcondicaoPagamento I ON             
			I.Empresa = A.Empresa AND             
			I.Codigo = A.CodigocondicaoPagamento

	[:FILTRO]