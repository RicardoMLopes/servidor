colunas_cadusers = {
    "id": "INT AUTO_INCREMENT PRIMARY KEY",
    "empresa": "INT NOT NULL",
    "codigovendedor": "CHAR(6) NOT NULL",
    "usuario": "VARCHAR(50) NOT NULL UNIQUE",
    "senha": "VARCHAR(255) NOT NULL",
    "novasenha": "VARCHAR(255)",
    "email": "VARCHAR(255)",
    "token": "VARCHAR(255)",
    "situacaoregistro": "VARCHAR(20) NOT NULL DEFAULT 'ativo'",
    "dataregistro": "DATETIME DEFAULT NULL"
}