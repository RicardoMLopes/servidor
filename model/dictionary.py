import logging
from sqlalchemy import text
from params.logger_config import logger


def criar_tabela_cadusers_se_nao_existir(db, nome_tabela: str, colunas_esperadas: dict, pk_colunas: list = None):
    """
    Cria a tabela se não existir. Se já existir, garante que todas as colunas definidas existem e estão com o tipo correto.
    Nunca altera PKs de tabelas existentes.

    :param db: sessão SQLAlchemy
    :param nome_tabela: nome da tabela
    :param colunas_esperadas: dicionário {coluna: tipo_sql}
    :param pk_colunas: lista de colunas que devem formar a PK se a tabela for criada
    """
    logging.warning("Entrou na rotina de criação/verificação da tabela %s.", nome_tabela)

    try:
        # 1️⃣ Verifica se a tabela existe
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
            # Cria tabela do zero, incluindo PK
            colunas_sql = []
            for col, definicao in colunas_esperadas.items():
                if definicao.upper().startswith("DATETIME") and "DEFAULT" not in definicao.upper():
                    definicao += " DEFAULT CURRENT_TIMESTAMP"
                colunas_sql.append(f"{col} {definicao}")

            pk_sql = f", PRIMARY KEY ({', '.join(pk_colunas)})" if pk_colunas else ""

            create_sql = f"""
                CREATE TABLE {nome_tabela} (
                    {', '.join(colunas_sql)}
                    {pk_sql}
                ) ENGINE=MyISAM DEFAULT CHARSET=latin1;
            """
            db.execute(text(create_sql))
            db.commit()
            logger.info("Tabela %s criada com sucesso.", nome_tabela)
            return

        # 2️⃣ Tabela existe → verifica colunas
        logger.info("Tabela %s já existe. Verificando colunas...", nome_tabela)
        colunas_existentes = db.execute(
            text("""
                SELECT column_name, column_type, is_nullable, column_default, extra
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                  AND table_name = :nome_tabela
            """),
            {"nome_tabela": nome_tabela}
        ).fetchall()

        colunas_existentes_dict = {
            c[0].lower(): {"type": c[1].upper(), "nullable": c[2], "default": c[3], "extra": c[4]}
            for c in colunas_existentes
        }

        alteracoes = False

        for coluna, definicao in colunas_esperadas.items():
            coluna_lower = coluna.lower()
            definicao_upper = definicao.upper()

            if coluna_lower not in colunas_existentes_dict:
                # Não adiciona AUTO_INCREMENT em tabelas existentes
                if "AUTO_INCREMENT" in definicao_upper:
                    logger.info("Coluna %s é AUTO_INCREMENT. Não será adicionada em tabela existente.", coluna)
                    continue
                # Ajusta DATETIME
                if definicao_upper.startswith("DATETIME") and "DEFAULT" not in definicao_upper:
                    definicao += " DEFAULT NULL"
                db.execute(text(f"ALTER TABLE {nome_tabela} ADD COLUMN {coluna} {definicao};"))
                logger.info("Coluna %s adicionada em %s.", coluna, nome_tabela)
                alteracoes = True
            else:
                logger.info("Coluna %s já existe. Nenhuma ação necessária.", coluna)

        if alteracoes:
            db.commit()
            logger.info("Atualização de colunas em %s concluída.", nome_tabela)
        else:
            logger.info("Todas as colunas de %s estão corretas. Nenhuma alteração necessária.", nome_tabela)

    except Exception as e:
        db.rollback()
        logger.error("Erro ao criar/atualizar tabela %s: %s", nome_tabela, e)
        raise
