MODELS_PARAMETRO = {
    "cadparametro": {
        "required_columns": {
            "id": "INT AUTO_INCREMENT PRIMARY KEY",
            "empresa": "INT NOT NULL",
            "vendedorPadrao": "CHAR(6)",
            "controlaSaldoEstoque": "BIT(1) NOT NULL DEFAULT b'1'",
            "casaDecimalQuantidade": "INT(1) NOT NULL DEFAULT 0",
            "casaDecimalValor": "INT(1) NOT NULL DEFAULT 2",
            "percentualDescontoVenda": "DOUBLE(15,6) NOT NULL DEFAULT 0",
            "datacatalogo": "DATETIME",
            "situacaoRegistro": "CHAR(1) NOT NULL DEFAULT 'I'",
            "dataRegistro": "DATETIME NOT NULL"
        },
        "primary_keys": ["id", "empresa"],  # id + empresa como PK composta
        "id_optional": True  # se faltar id, não atualiza (mesma lógica do cliente)
    }
}
