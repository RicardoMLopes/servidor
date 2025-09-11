MODELS_EMPRESA = {
    "cadempresa": {
        "required_columns": {
            "codigo": "VARCHAR(255)",
            "nome": "VARCHAR(255)",
            "cnpj": "VARCHAR(255)",
            "rua": "VARCHAR(255)",
            "numero": "VARCHAR(255)",
            "bairro": "VARCHAR(255)",
            "cidade": "VARCHAR(255)",
            "telefone": "VARCHAR(255)",
            "email": "VARCHAR(255)"
        },
        "primary_keys": ["id"],  # id será autoincrement
        "id_optional": True
    }
}
