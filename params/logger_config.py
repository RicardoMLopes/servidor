import logging

# Criação do logger
logger = logging.getLogger("ibvendas")
logger.setLevel(logging.INFO)

# Evita adicionar múltiplos handlers se o módulo for importado várias vezes
if not logger.hasHandlers():
    # Criação do handler de console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formatação do log
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)

    # Adiciona o handler ao logger
    logger.addHandler(console_handler)

# Bloco de teste
if __name__ == "__main__":
    logger.info("Logger funcionando corretamente no modo standalone.")