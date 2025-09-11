MODELS_VEND = {
    "cadvendedor": {
        "required_columns": {
            "empresa": "INT NOT NULL",
            "codigo": "CHAR(6) NOT NULL",
            "cd_rota": "DECIMAL(10,0)",
            "nome": "VARCHAR(80) NOT NULL",
            "situacaoRegistro": "CHAR(1) DEFAULT 'I'",
            "dataRegistro": "DATETIME",
        },
        "primary_keys": ["empresa", "codigo"],
         "id_optional": True  # Se faltar id, ignora alterações
    }
}
