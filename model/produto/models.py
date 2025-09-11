MODELS_PROD  = {"cadproduto": {
    "required_columns": {
        "empresa": "INT NOT NULL",
        "codigo": "CHAR(6) NOT NULL",
        "descricao": "VARCHAR(500) NOT NULL",
        "unidadeMedida": "CHAR(3)",
        "codigoBarra": "CHAR(20)",
        "agrupamento": "VARCHAR(60)",
        "marca": "VARCHAR(60)",
        "modelo": "VARCHAR(60)",
        "tamanho": "VARCHAR(20)",
        "cor": "VARCHAR(20)",
        "peso": "DOUBLE(15,6) NOT NULL DEFAULT 0",
        "precoVenda": "DOUBLE(15,6) NOT NULL DEFAULT 0",
        "percentualDesconto": "DOUBLE(15,6) NOT NULL DEFAULT 0",
        "estoque": "DOUBLE(15,6) NOT NULL DEFAULT 0",
        "reajustaCondicaoPagamento": "CHAR(1) NOT NULL DEFAULT 'N'",
        "percentualComissao": "DOUBLE(15,6) NOT NULL DEFAULT 0",
        "situacaoRegistro": "CHAR(1) NOT NULL DEFAULT 'I'",
        "dataRegistro": "DATETIME NOT NULL",
        },
    "primary_keys": ["empresa", "codigo"],  # Para criar a PK
     "id_optional": True  # Se faltar id, ignora alterações
    }
}
