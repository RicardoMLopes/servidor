   SELECT A.NumeroDocumento,'XXX' AS TipoMovimentacao, A.Movimentacao,
       A.CodigoFornecCliente, A.Serie, A.Modelo, A.DataEmissao,
       A.CodigoCondicaoPagamento, A.ResponsavelFrete, A.Transportadora,
       A.ValorFrete AS A2ValorFrete, A.Placa, A.AliquotaICMSFrete AS A2AliquotaICMSFrete, 
       A.ValorICMSFrete AS A2ValorICMSFrete, A.ValorDespesas AS A2ValorDespesas, 
       'Valor de desconto da Nota:' As TituloDesconto, A.ValorDesconto AS A2ValorDesconto,
       A.Vendedor, A.ValorTotal AS A2ValorTotal,      
       A.BaseCalculoICMS As A2BaseCalculoICMS, A.AliquotaICMS AS A2AliquotaICMS, A.ValorICMS AS A2ValorICMS, 
       A.ValorIPI AS A2ValorIPI, A.ValorDocumento AS A2ValorDocumento,
       A.ValorDocumento As EXTENSO001,
       A.ValorDocumento As EXTENSO041,
       A.ValorDocumento As EXTENSO081,       
       A.CFOP, A.BaseCalculoICMSSubstituic AS A2BaseCalculoICMSSubstitu, 
       A.ValorICMSSubstituicao AS A2ValorICMSSubstituicao, 
       A.ValorICMSComplementar AS A2ValorICMSComplementar,
       A.ValorSeguro AS A2ValorSeguro, A.ValorIsensao AS A2ValorIsensao, 
       C.Nome AS NomeCliente, C.Endereco, C.Bairro, C.Cidade,
       C.Telefone, C.CNPJCPF, C.InscricaoEstadual, C.UF, C.CEP,
       E.Descricao AS DescicaoCFOP, 
       F.Nome AS NomeTransportadora, F.CnpjCpf AS CNPJTransporte,
       F.UF AS UFTransportadora, F.Endereco AS EndTransportadora,
       F.Cidade AS CidTransportadora, F.InscricaoEstadual AS InsEstTransportadora,	 
       SUBSTRING(A.Observacao FROM 1 FOR 62) As Observacao,
       SUBSTRING(A.Observacao FROM 63 FOR 62) As Observacao1,
       SUBSTRING(A.Observacao FROM 125 FOR 45) As Observacao2,
       SUBSTRING(A.Observacao FROM 170 FOR 45) As Observacao3,
       SUBSTRING(A.Observacao FROM 215 FOR 45) As Observacao4,
       0 AS A2ValorTotalProdutos,
       0 AS A0NumeroFin1, 0 AS A0NumeroFin2, 0 AS A0NumeroFin3,
       '' AS DataVencimentoFin1, '' AS DataVencimentoFin2, '' AS DataVencimentoFin3,
       0 AS A2ValorFin1, 0 AS A2ValorFin2, 0 AS A2ValorFin3, 
       '' AS NomeServico, '' AS UnidadeServico, 0 AS A2QtdServico, 0 AS A2ValorServico,
       0 AS A2ValorTotalServico, 0 AS A2BaseCalculoICMS, 0 AS A2ValorISSServico,
       0 AS A2BCServicoISS, 0 AS A2AliquotaISSServico, 0 As A2ValorISSServico, 0 AS A2ValorTotalDoServic
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
