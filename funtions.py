import hashlib
import re
import time
from connection import DB_CHAVE
from fastapi.templating import Jinja2Templates




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


templates.env.filters["formata_cnpj"] = formata_cnpj