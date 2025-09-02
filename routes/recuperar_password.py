from params.logger_config import logger
import secrets
from datetime import datetime
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import text

from function.funtions import templates, hash_password, limpa_cnpj
from params.alerta import enviar_alerta
from database.querys import ConsultaUsuarioPorUsername
from function.funtions import gerar_token_cnpj
from database.dependencies import get_nome_banco_por_token, get_empresa_session
from database.connection import DB_CHAVE

recuperaruser_router = APIRouter()


# ===============================
# GET -> Formulário de recuperação
# ===============================
@recuperaruser_router.get("/", response_class=HTMLResponse)
async def mostrar_form_recuperar_senha(request: Request, cnpj: str = ""):
    empresa = None
    if cnpj:
        # Limpa o CNPJ e gera token
        cnpj = limpa_cnpj(cnpj)
        token = gerar_token_cnpj(cnpj, DB_CHAVE)
        nome_banco = get_nome_banco_por_token(token)
        session_empresa = get_empresa_session(nome_banco)

        with session_empresa as db:
            # Consulta empresa usando text()
            empresa_raw = db.execute(
                text("SELECT * FROM cadempresa WHERE cnpj=:cnpj"),
                {"cnpj": cnpj}
            ).mappings().all()

            if empresa_raw:
                empresa = empresa_raw[0]

    return templates.TemplateResponse("recuperar_password.html", {
        "request": request,
        "form_data": {"cnpj": cnpj},
        "errors": {},
        "empresa": empresa
    })


# ===============================
# POST -> Envia nova senha por e-mail
# ===============================
@recuperaruser_router.post("/", response_class=HTMLResponse)
async def esqueci_senha(request: Request, cnpj: str = Form(...), usuario: str = Form(...)):
    errors = {}
    form_data = {"cnpj": cnpj, "usuario": usuario}

    # Limpa CNPJ, gera token e obtém sessão do banco
    cnpj = limpa_cnpj(cnpj)
    token = gerar_token_cnpj(cnpj, DB_CHAVE)
    nome_banco = get_nome_banco_por_token(token)
    session_empresa = get_empresa_session(nome_banco)

    with session_empresa as db:
        # Consulta usuário
        user_raw = ConsultaUsuarioPorUsername(db, usuario)
        if not user_raw:
            errors["usuario"] = "Usuário não encontrado."
            return templates.TemplateResponse("recuperar_password.html", {
                "request": request,
                "errors": errors,
                "form_data": form_data
            })

        # Gera senha temporária
        nova_senha = secrets.token_urlsafe(8).upper()
        nova_senha = nova_senha.upper()
        logger.warning(f"Nova senha temporária gerada para {usuario}: {nova_senha}")
        nova_senha_hash = hash_password(nova_senha)
        dataatual = datetime.now()

        # Atualiza senha no banco
        sql = text("UPDATE cadusers SET novasenha = :novasenha, dataregistro = :data WHERE usuario = :usuario")
        resultado = db.execute(sql, {"usuario": usuario, "novasenha": nova_senha_hash, "data": dataatual})
        db.commit()

        # Verifica se algum usuário foi atualizado
        if resultado.rowcount == 0:
            errors["db"] = "Erro ao atualizar senha no banco."
            return templates.TemplateResponse("recuperar_password.html", {
                "request": request,
                "errors": errors,
                "form_data": form_data
            })

        # Envia e-mail
        try:
            email_destino = user_raw[0]["email"]
            enviar_alerta(
                assunto="Recuperação de Senha",
                mensagem=f"Sua nova senha temporária é: {nova_senha}\nPor favor, altere após o login.",
                to=email_destino
            )
        except Exception as e:
            errors["email"] = f"Erro ao enviar e-mail: {str(e)}"
            return templates.TemplateResponse("recuperar_password.html", {
                "request": request,
                "errors": errors,
                "form_data": form_data
            })

    # Sucesso
    return templates.TemplateResponse("sucesso.html", {
        "request": request,
        "usuario": usuario
    })
