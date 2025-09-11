# models_config.py
MODELS_CLIENT = {
    "cadcliente": {
        "required_columns": {
            "empresa": "INT NOT NULL",
            "codigo": "CHAR(6) NOT NULL",
            "codigovendedor": "CHAR(6) DEFAULT '0'",
            "nome": "VARCHAR(250) NOT NULL",
            "contato": "VARCHAR(250)",
            "cpfCnpj": "CHAR(14)",
            "rua": "VARCHAR(80)",
            "numero": "CHAR(7)",
            "bairro": "VARCHAR(80)",
            "cidade": "VARCHAR(80)",
            "estado": "VARCHAR(30)",
            "telefone": "VARCHAR(30)",
            "limiteCredito": "DECIMAL(12,2) DEFAULT 0",
            "observacao": "VARCHAR(500)",
            "restricao": "VARCHAR(250)",
            "reajuste": "DECIMAL(5,2) DEFAULT 0",
            "situacaoRegistro": "CHAR(1) DEFAULT 'A'",
            "dataRegistro": "DATETIME",
            "versao": "BIGINT DEFAULT 1"
        },
        "id_optional": True  # Se faltar id, ignora alterações
    }
}
