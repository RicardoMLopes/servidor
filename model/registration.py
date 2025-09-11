import logging
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

# Configura o logging (uma vez no seu main ou módulo de inicialização)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def validar_tabela(db: Session, tabela: str, config: dict):
    """
    Valida a estrutura de uma tabela:
      - Se não existir: cria (ainda precisa de Base.metadata.create_all)
      - Se existir sem 'id' (banco antigo): ignora alterações
      - Se existir e faltar colunas: adiciona colunas
    """
    insp = inspect(db.bind)

    if not insp.has_table(tabela):
        logging.warning(f"⚠️ Tabela {tabela} não encontrada. Precisa criar via model declarativo.")
        return

    existentes = [col["name"] for col in insp.get_columns(tabela)]

    # Verifica banco antigo sem ID
    if config.get("id_optional") and "id" not in existentes:
        logging.warning(f"🔹 {tabela}: Banco antigo sem ID → ignorando alterações")
        return

    # Adiciona colunas que faltam
    for colname, colsql in config["required_columns"].items():
        if colname not in existentes:
            sql = f"ALTER TABLE {tabela} ADD COLUMN {colname} {colsql}"
            db.execute(text(sql))
            db.commit()
            logging.info(f"✅ Coluna {colname} adicionada em {tabela}")
