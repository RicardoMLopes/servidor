from fastapi import Form, Request, HTTPException
from fastapi.params import Depends
from fastapi.responses import HTMLResponse
from requests import Session
import traceback
from fastapi import APIRouter, Query
from starlette.responses import JSONResponse
from database.dependencies import get_empresa_session, get_nome_banco_por_token, get_empresa_db
from params.logger_config import logger
from model.dictionary import criar_tabela_cadusers_se_nao_existir
from model.cadusers import colunas_cadusers
from database.querys import ConsultaVendedores, ConsultaEmpresaPorCNPJ, inserir_usuario, Consultausers, \
    ConsultaUsuarioPorUsername, atualizar_senha_usuario, ConsultaUsuarioPorVendedor, Consultar_vendedor_user, \
    usuario_existe
from function.funtions import gerar_token_cnpj, hash_password, gerar_token_usuario, verificar_senha, limpa_cnpj
from function.funtions import templates
from database.connection import  DB_CHAVE


cadusers_router = APIRouter()
sincronizaruser_router = APIRouter()
alterarsenha_router = APIRouter()


# Passo 1: Tela para digitar o CNPJ
@cadusers_router.get("/", response_class=HTMLResponse)
def tela_cnpj(request: Request):
    return templates.TemplateResponse("login/cnpj.html", {
        "request": request,
        "error": None
    })

@cadusers_router.post("/buscar-vendedores", response_class=HTMLResponse)
def buscar_vendedores(request: Request, cnpj: str = Form(...)):
    # gera token
    token = gerar_token_cnpj(cnpj, DB_CHAVE)
    print("Token:", token)

    # busca nome banco pelo token
    nome_banco = get_nome_banco_por_token(token)

    # cria sessão empresa
    session_empresa = get_empresa_session(nome_banco)
    with session_empresa as db:

        empresa_raw = ConsultaEmpresaPorCNPJ(db, cnpj)
        if not empresa_raw:
            return templates.TemplateResponse("cnpj.html", {
                "request": request,
                "error": "Empresa não encontrada para o CNPJ informado."
            })

        empresa = empresa_raw[0]  # pega o primeiro registro (dict)

        vendedores_raw = Consultar_vendedor_user(db)
        vendedores = [{"id": v["codigo"], "nome": v["nome"]} for v in vendedores_raw]

    # Preencher form_data com cnpj para o campo readonly no form
    form_data = {"cnpj": cnpj}

    return templates.TemplateResponse("cadusuario.html", {
        "request": request,
        "empresa": empresa,
        "empresa_nome": empresa.get("nome", ""),  # passa o nome para o input readonly
        "vendedores": vendedores,
        "errors": {},
        "form_data": form_data
    })


# Passo 2: Cadastro do usuário
@cadusers_router.post("/cadastrar", response_class=HTMLResponse)
async def cadastrar_usuario(
    request: Request,
    cnpj: str = Form(...),
    vendedor_id: str = Form(...),
    usuario: str = Form(...),
    senha: str = Form(...),
    email: str = Form(...),
    confirmar_senha: str = Form(...)
):
    errors = {}
    form_data = {
        "cnpj": cnpj,
        "vendedor_id": vendedor_id,
        "usuario": usuario,
        "email": email
    }

    # Validação básica
    if senha != confirmar_senha:
        errors["confirmar_senha"] = "A senha e a confirmação não conferem."
    if len(senha) < 6:
        errors["senha"] = "A senha deve ter pelo menos 6 caracteres."
    if not usuario:
        errors["usuario"] = "Usuário é obrigatório."

    token = gerar_token_cnpj(cnpj, DB_CHAVE)
    nome_banco = get_nome_banco_por_token(token)
    session_empresa = get_empresa_session(nome_banco)

    with session_empresa as db:
        empresa_raw = ConsultaEmpresaPorCNPJ(db, cnpj)
        if not empresa_raw:
            errors["cnpj"] = "Empresa não encontrada para o CNPJ informado."
            empresa = None
        else:
            empresa = empresa_raw[0]

        vendedores_raw = ConsultaVendedores(db)
        vendedores = [{"id": v["codigo"], "nome": v["nome"]} for v in vendedores_raw]

        if errors:
            return templates.TemplateResponse("cadusuario.html", {
                "request": request,
                "empresa": empresa,
                "empresa_nome": empresa.get("nome") if empresa else "",
                "vendedores": vendedores,
                "errors": errors,
                "form_data": form_data
            })

        if usuario_existe(db, usuario):
            errors["usuario"] = "Este nome de usuário já está em uso. Tente outro diferente."
            return templates.TemplateResponse("cadusuario.html", {
                "request": request,
                "empresa": empresa,
                "empresa_nome": empresa.get("nome") if empresa else "",
                "vendedores": vendedores,
                "errors": errors,
                "form_data": form_data
            })

        senha_hash = hash_password(senha)
        token = gerar_token_usuario(usuario, vendedor_id, empresa["codigo"])
        sucesso = inserir_usuario(db, empresa["codigo"], vendedor_id, usuario, email, senha_hash, token)

        if not sucesso:
            errors["db"] = "Erro ao salvar usuário no banco."
            return templates.TemplateResponse("cadusuario.html", {
                "request": request,
                "empresa": empresa,
                "empresa_nome": empresa.get("nome"),
                "vendedores": vendedores,
                "errors": errors,
                "form_data": form_data
            })

    return templates.TemplateResponse("sucesso.html", {
        "request": request,
        "usuario": usuario
    })

# ==============================================================
# ROTINA PARA SINCRONIZAR O USUÁRIO
# ---------------------------------------------------------------
@sincronizaruser_router.get("")
async def sincronizar_usuarios( db: Session = Depends(get_empresa_db)):
    """
    Retorna todos os usuários da empresa especificada.
    """
    try:
        # Consulta todos os usuários da empresa
        resultado = Consultausers(db)

        if not resultado or len(resultado) == 0:
            raise HTTPException(status_code=404, detail="Nenhum usuário encontrado para esta empresa")

        # Formata a resposta
        usuarios_lista = []
        for u in resultado:
            usuarios_lista.append({
                "empresa": u.empresa,
                "codigovendedor": u.codigovendedor,
                "usuario": u.usuario,
                "senha": u.senha,
                "novasenha": u.novasenha,
                "email": u.email,
                "situacaoregistro": u.situacaoregistro,
                "token": u.token,
                "dataregistro": u.dataregistro.isoformat() if u.dataregistro else None
            })

        return usuarios_lista

    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno: {e.__class__.__name__}: {str(e)}")



# ======================================================================
# ROTINA PARA RECUPERAR SENHA OU ALTERAR A SENHA
# ----------------------------------------------------------------------
@alterarsenha_router.post("", response_class=HTMLResponse)
async def alterar_senha(
        request: Request,
        cnpj: str = Form(...),
        usuario: str = Form(...),
        senha_atual: str = Form(...),
        nova_senha: str = Form(...),
        email: str = Form(...),
        confirmar_senha: str = Form(...),
        vendedor_id: str = Form(...)

):
    errors = {}
    form_data = {
        "cnpj": cnpj,
        "usuario": usuario
    }
    cnpj = limpa_cnpj(cnpj)
    # Validação básica
    if nova_senha != confirmar_senha:
        errors["confirmar_senha"] = "A nova senha e a confirmação não conferem."
    if len(nova_senha) < 6:
        errors["nova_senha"] = "A senha deve ter pelo menos 6 caracteres."
    if not usuario:
        errors["usuario"] = "Usuário é obrigatório."
    if not cnpj:
        errors["cnpj"] = "CNPJ é obrigatório."
    if not email:
        errors["email"] = "E-mail é obrigatório."

    # Buscar empresa e abrir sessão
    token = gerar_token_cnpj(cnpj, DB_CHAVE)
    nome_banco = get_nome_banco_por_token(token)
    session = get_empresa_session(nome_banco)

    with session as db:
        # Busca empresa
        empresa_raw = ConsultaEmpresaPorCNPJ(db, cnpj)
        empresa = empresa_raw[0] if empresa_raw else None
        if not empresa:
            errors["cnpj"] = "Empresa não encontrada para o CNPJ informado."

        # Buscar usuário
        user_raw = ConsultaUsuarioPorUsername(db, usuario)
        if not user_raw:
            errors["usuario"] = "Usuário não encontrado."
        else:
            user = user_raw[0]
            logger.warning("Senha digitada: %s", senha_atual)
            logger.warning("Hash no banco: %s", user["novasenha"])
            logger.warning("Resultado verificar_senha: %s", verificar_senha(senha_atual, user["novasenha"]))

            # Verificar senha atual
            if not verificar_senha(senha_atual, user["novasenha"]):
                errors["senha_atual"] = "Senha atual incorreta."

        if errors:
            # Buscar lista de vendedores para o select
            vendedores = ConsultaVendedores(db)
            return templates.TemplateResponse("alterarpassword.html", {
                "request": request,
                "errors": errors,
                "form_data": form_data,
                "empresa": empresa,
                "vendedores": vendedores
            })

        # Atualizar senha
        print("nova senha: ", nova_senha)
        nova_senha_hash = hash_password(nova_senha)
        sucesso = atualizar_senha_usuario(db, usuario, nova_senha_hash)

        if not sucesso:
            errors["db"] = "Erro ao atualizar senha no banco."
            vendedores = ConsultaVendedores(db)
            return templates.TemplateResponse("alterarpassword.html", {
                "request": request,
                "errors": errors,
                "form_data": form_data,
                "empresa": empresa,
                "vendedores": vendedores
            })

    # Sucesso
    return templates.TemplateResponse("sucesso.html", {
        "request": request,
        "usuario": usuario
    })



@alterarsenha_router.get("", response_class=HTMLResponse)
async def mostrar_form_recuperar_senha(request: Request, cnpj: str):
 #   logger.warning("Entrou aqui! mostrar form recuperar senha...")
    empresa = None
    vendedores = []
    cnpj = limpa_cnpj(cnpj)
    # Cria sessão baseada no token do CNPJ
    token = gerar_token_cnpj(cnpj, DB_CHAVE)
    nome_banco = get_nome_banco_por_token(token)
    session_empresa = get_empresa_session(nome_banco)

    with session_empresa as db:
        empresa_raw = ConsultaEmpresaPorCNPJ(db, cnpj)
        if empresa_raw:
            empresa = empresa_raw[0]
            vendedores_raw = ConsultaVendedores(db)
            vendedores = [{"id": v["codigo"], "nome": v["nome"]} for v in vendedores_raw]

    return templates.TemplateResponse("alterarpassword.html", {
        "request": request,
        "empresa": empresa,
        "vendedores": vendedores,
        "form_data": {"cnpj": cnpj},
        "errors": {}
    })

@alterarsenha_router.get("/", response_class=JSONResponse)
async def buscar_usuario_vendedor(cnpj: str = Query(...), vendedor_id: str = Query(...)):
    cnpj = limpa_cnpj(cnpj)
#    logger.warning("Entrou na função ConsultaUsuarioPorVendedor")


#    logger.warning("CNPJ recebido:", cnpj)
#    logger.warning("Vendedor ID recebido:", vendedor_id)

    token = gerar_token_cnpj(cnpj, DB_CHAVE)
    nome_banco = get_nome_banco_por_token(token)
    session_empresa = get_empresa_session(nome_banco)

    with session_empresa as db:
        resultado = ConsultaUsuarioPorVendedor(db, vendedor_id)

        if resultado and len(resultado) > 0:
            usuario = resultado[0]["usuario"]
            email = resultado[0]["email"]
            return {"usuario": usuario, "email": email}
        else:
            return {"usuario": "", "email": ""}





