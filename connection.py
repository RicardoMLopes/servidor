from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
from model.pedido import Base



# ✅ Carrega variáveis de ambiente
load_dotenv()
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "")
DB_CHAVE = os.getenv("DB_CHAVE", "")


DB_PASSWORD = quote_plus(DB_PASSWORD)

# Sessão para o banco central de controle (fixo)
def get_controle_session():
    print("nome database controle_session: ", DB_NAME)
    # ✅ Validação básica de variáveis ausentes
    missing_vars = [var for var in ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"] if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Variáveis de ambiente ausentes: {', '.join(missing_vars)}")

    # ✅ Corrigida a URL com charset compatível
    DATABASE_URL = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8"
    )
    print("DATABASE_URL:", DATABASE_URL.replace(DB_PASSWORD, "*****"))

    engine = create_engine(DATABASE_URL, echo=True)
    Base.metadata.bind = engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def get_empresa_session(db_name: str):

    # ✅ Verifica apenas as variáveis de ambiente reais
    missing_vars = [var for var in ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT"] if not os.getenv(var)]
    if not db_name:
        missing_vars.append("NOME DO BANCO (db_name)")
    if missing_vars:
        raise ValueError(f"Variáveis de ambiente ausentes: {', '.join(missing_vars)}")

    DATABASE_URL = (
        f"mysql+pymysql://{db_name}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{db_name}?charset=utf8"
    )
    print("🔗 Conectando no banco:", DATABASE_URL.replace(DB_PASSWORD, "*****"))

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    Base.metadata.bind = engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()