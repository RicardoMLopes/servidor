from sqlalchemy import text

def criar_tabela_cadusers_se_nao_existir(db, nome_tabela, colunas_esperadas):
    """
    Cria a tabela se não existir.
    Se já existir, garante que todas as colunas definidas em colunas_esperadas existem.
    colunas_esperadas = {nome_coluna: definição_SQL}
    """

    try:
        # Verifica se a tabela existe
        tabela_existe = db.execute(
            text("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                  AND table_name = :nome_tabela
            """),
            {"nome_tabela": nome_tabela}
        ).scalar()

        if tabela_existe == 0:
            # Cria a tabela inteira com as colunas definidas
            colunas_sql = ",\n    ".join(
                f"{col} {definicao}" for col, definicao in colunas_esperadas.items()
            )
            create_sql = f"""
                CREATE TABLE {nome_tabela} (
                    {colunas_sql}
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            db.execute(text(create_sql))
            db.commit()
            print(f"Tabela {nome_tabela} criada com sucesso.")
        else:
            print(f"Tabela {nome_tabela} já existe. Verificando colunas...")

            # Pega colunas existentes
            colunas_existentes = db.execute(
                text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = DATABASE()
                      AND table_name = :nome_tabela
                """),
                {"nome_tabela": nome_tabela}
            ).fetchall()
            colunas_existentes = {c[0] for c in colunas_existentes}

            # Cria colunas que não existem
            for coluna, definicao in colunas_esperadas.items():
                if coluna not in colunas_existentes:
                    print(f"Adicionando coluna {coluna} em {nome_tabela}...")
                    db.execute(text(f"ALTER TABLE {nome_tabela} ADD COLUMN {coluna} {definicao};"))

            db.commit()
            print("Verificação concluída.")

    except Exception as e:
        db.rollback()
        print(f"Erro ao criar/atualizar tabela {nome_tabela}: {e}")
