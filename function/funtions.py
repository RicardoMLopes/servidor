import hashlib
import unicodedata
import re
import time
from database.connection import DB_CHAVE
from fastapi.templating import Jinja2Templates
from datetime import datetime
from typing import Optional, Union




templates = Jinja2Templates(directory="templates")



# Salt fixo, deve ser o mesmo que no app
SALT = DB_CHAVE

def hash_password(password: str) -> str:
    """
    Gera hash determinístico da senha com SHA-256 + salt fixo.
    """
    return hashlib.sha256((SALT + password).encode('utf-8')).hexdigest()


def verificar_senha(password_digitada: str, hash_armazenado: str) -> bool:
    """
    Valida se a senha digitada corresponde ao hash armazenado.
    """
    if not hash_armazenado:
        return False
    hash_digitado = hash_password(password_digitada)
    return hash_digitado == hash_armazenado

def gerar_token_cnpj(cnpj: str, chave_secreta: str) -> str:
    # Remove tudo que não for dígito do CNPJ
    cnpj_limpo = re.sub(r'\D', '', cnpj)
    texto = cnpj_limpo + chave_secreta
    hash_sha256 = hashlib.sha256(texto.encode('utf-8')).hexdigest()
    return hash_sha256

def formata_cnpj(cnpj: str) -> str:
    cnpj_limpo = re.sub(r'\D', '', cnpj)  # só números
    if len(cnpj_limpo) != 14:
        return cnpj  # retorna original se não tiver 14 dígitos
    return f"{cnpj_limpo[:2]}.{cnpj_limpo[2:5]}.{cnpj_limpo[5:8]}/{cnpj_limpo[8:12]}-{cnpj_limpo[12:]}"

def limpa_cnpj(cnpj: str) -> str:
    return re.sub(r'\D', '', cnpj)  # Remove tudo que não é dígito


def gerar_token_usuario(usuario: str, codigovendedor: str, codigo_empresa: str) -> str:
    timestamp = str(int(time.time()))  # timestamp em segundos
    raw_string = f"{usuario}{codigovendedor}{codigo_empresa}{DB_CHAVE}{timestamp}"
    token = hashlib.sha256(raw_string.encode('utf-8')).hexdigest()
    return token


def converter_data_mysql(data: Optional[Union[str, datetime]]) -> Optional[str]:
    """
    Converte uma data ISO 8601 ou datetime para string compatível com MySQL DATETIME.

    Exemplos de entrada aceitos:
    - '2025-08-15T00:14:42.948Z'
    - '2025-08-15T00:14:42'
    - datetime(2025, 8, 15, 0, 14, 42)

    Retorna string no formato 'YYYY-MM-DD HH:MM:SS' ou None se entrada inválida.
    """
    if not data:
        return None

    # Se for datetime, formata direto
    if isinstance(data, datetime):
        return data.strftime("%Y-%m-%d %H:%M:%S")

    # Se for string, remove 'Z' e milissegundos
    try:
        # Remove 'Z' e divide milissegundos
        if "T" in data:
            data = data.split(".")[0].replace("T", " ")
        dt = datetime.strptime(data, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def limpar_texto_mysql_auto(texto: str) -> str:
    if not texto:
        return ""

        # Normaliza texto
    texto = unicodedata.normalize("NFKC", texto)

    # Remove caracteres de controle e não imprimíveis
    texto = "".join(c for c in texto if unicodedata.category(c)[0] != "C")

    # Remove aspas simples e duplas
    texto = texto.replace("'", "").replace('"', "")

    # Mantém apenas letras, números, espaços e pontuação segura
    texto = re.sub(r"[^a-zA-Z0-9\sáàãâéêíóôõúüçÁÀÃÂÉÊÍÓÔÕÚÜÇ_\-.,;:@!?/\\()\[\]]+", "", texto)

    # Remove espaços duplicados
    texto = " ".join(texto.split())
    print(texto)
    return texto



templates.env.filters["formata_cnpj"] = formata_cnpj



