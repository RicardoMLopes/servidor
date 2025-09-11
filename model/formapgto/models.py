MODELS_FORMA = {
    "cadcondicaopagamento": {
        "required_columns": {
            "empresa": "INT NOT NULL",
            "codigo": "CHAR(6) NOT NULL",
            "descricao": "VARCHAR(40)",
            "acrescimo": "DECIMAL(15,4) NOT NULL DEFAULT 0",
            "desconto": "DECIMAL(15,4) NOT NULL DEFAULT 0",
            "situacaoRegistro": "CHAR(1) NOT NULL DEFAULT 'I'",
            "dataRegistro": "DATETIME"
        },
        "primary_keys": ["empresa", "codigo"],
        "id_optional": True  # Se faltar id, ignora alterações
    }
}
