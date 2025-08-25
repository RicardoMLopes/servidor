from sqlalchemy import text

def criar_tabela_cadusers_se_nao_existir(db):
    try:
        tabela_existe = db.execute(
            text("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                  AND table_name = 'cadusers'
            """)
        ).scalar()

        if tabela_existe == 0:
            db.execute(text("""
                CREATE TABLE cadusers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    empresa INT NOT NULL,
                    codigovendedor CHAR(6) NOT NULL,
                    usuario VARCHAR(50) NOT NULL UNIQUE,
                    senha VARCHAR(255) NOT NULL,
                    novasenha VARCHAR(255),
                    email VARCHAR(255),
                    token VARCHAR(255),
                    situacaoregistro VARCHAR(20) NOT NULL DEFAULT 'ativo',
                    dataregistro DATETIME DEFAULT NULL
                ) ENGINE=MyISAM DEFAULT CHARSET=latin1;


            """))
            db.commit()
            print("Tabela cadusers criada com sucesso.")
        else:
            print("Tabela cadusers já existe.")

    except Exception as e:
        db.rollback()
        print(f"Erro ao criar tabela cadusers: {e}")
