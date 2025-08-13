from fastapi import APIRouter, Form, Request, HTTPException
from fastapi.params import Depends
from fastapi.responses import HTMLResponse
from requests import Session
import traceback
from dependencies import get_empresa_session, get_nome_banco_por_token, get_empresa_db
from model.cadusers import criar_tabela_cadusers_se_nao_existir
from querys import ConsultaVendedores, ConsultaEmpresaPorCNPJ, inserir_usuario, Consultausers
from funtions import gerar_token_cnpj, hash_password, gerar_token_usuario
from funtions import templates
from connection import  DB_CHAVE


cadusers_router = APIRouter()
sincronizaruser_router = APIRouter()


# Passo 1: Tela para digitar o CNPJ
@cadusers_router.get("/", response_class=HTMLResponse)
def tela_cnpj(request: Request):
    return templates.TemplateResponse("cnpj.html", {
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
        criar_tabela_cadusers_se_nao_existir(db)

        empresa_raw = ConsultaEmpresaPorCNPJ(db, cnpj)
        if not empresa_raw:
            return templates.TemplateResponse("cnpj.html", {
                "request": request,
                "error": "Empresa não encontrada para o CNPJ informado."
            })

        empresa = empresa_raw[0]  # pega o primeiro registro (dict)

        vendedores_raw = ConsultaVendedores(db)
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
    confirmar_senha: str = Form(...)
):
    errors = {}
    form_data = {
        "cnpj": cnpj,
        "vendedor_id": vendedor_id,
        "usuario": usuario
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

        senha_hash = hash_password(senha)
        token = gerar_token_usuario(usuario, vendedor_id, empresa["codigo"])
        sucesso = inserir_usuario(db, empresa["codigo"], vendedor_id, usuario, senha_hash, token)

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
