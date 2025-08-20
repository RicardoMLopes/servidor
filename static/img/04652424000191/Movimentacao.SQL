Select *
	from MovNota
	where Empresa = :[C5]Empresa AND
		DataLancamento BETWEEN :[D]Data_Inicial AND :[D]Data_Final AND
		ValorDocumento >= :[N]Valor 
