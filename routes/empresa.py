from fastapi import APIRouter
from database.querys import ConsultaEmpresa, Insert_Empresa
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from database.dependencies import get_empresa_db
import traceback

from model.cadusers import colunas_cadusers

from model.cliente.cadcliente import c_Base
from model.cliente.models import MODELS_CLIENT

from model.dictionary import criar_tabela_cadusers_se_nao_existir
from model.empresa.cadempresa import empresa_Base
from model.empresa.models import MODELS_EMPRESA

from model.parametro.cadparametro import param_Base
from model.parametro.models import MODELS_PARAMETRO

from model.pedido.pedido import colunas_movnota, pks_movnota, colunas_movnotaitem, pks_movnotaitem

from model.produto.cadproduto import p_Base
from model.produto.models import MODELS_PROD

from model.vendedor.cadvendedor import v_Base
from model.vendedor.models import MODELS_VEND

from model.formapgto.cadformapagto import f_Base
from model.formapgto.models import MODELS_FORMA


from model.registration import validar_tabela
from params.alerta import enviar_alerta



empresa_router = APIRouter()

# Flags globais para controlar criação/verificação de tabelas
tabelas_inicializadas = {}

# requisição do cadastro de empresa
@empresa_router.get("")
async def buscar_empresa(db: Session = Depends(get_empresa_db)):
    try:

        resultado = ConsultaEmpresa(db)
        if resultado:
            # Verifica se as tabelas desse banco já foram inicializadas
            db_id = id(db.bind)  # identifica o banco pela engine
            if not tabelas_inicializadas.get(db_id):
                # Cria tabela do usuário
                criar_tabela_cadusers_se_nao_existir(db, "cadusers", colunas_cadusers)

                # Cria tabela de parâmetro
                param_Base.metadata.create_all(bind=db.bind)
                validar_tabela(db, "cadparametro", MODELS_PARAMETRO["cadparametro"])

                # 🔹 Cria/atualiza tabelas se necessário
                criar_tabela_cadusers_se_nao_existir(db, "movnota", colunas_movnota, pks_movnota)
                criar_tabela_cadusers_se_nao_existir(db, "movnotaitem", colunas_movnotaitem, pks_movnotaitem)

                # Cria tabela de cliente
                c_Base.metadata.create_all(bind=db.bind)
                validar_tabela(db, "cadcliente", MODELS_CLIENT["cadcliente"])

                # Cria tabela de produto
                p_Base.metadata.create_all(bind=db.bind)
                validar_tabela(db, "cadproduto", MODELS_PROD["cadproduto"])

                # Cria tabela de vendedor
                v_Base.metadata.create_all(bind=db.bind)
                validar_tabela(db, "cadvendedor", MODELS_VEND["cadvendedor"])

                # Cria tabela de forma pagto
                f_Base.metadata.create_all(bind=db.bind)
                validar_tabela(db, "cadcondicaopagamento", MODELS_FORMA["cadcondicaopagamento"])

            return {"codigo": resultado[0], "nome": resultado[1], "cnpj": resultado[2], "rua": resultado[3],
                    "numero": resultado[4], "bairro": resultado[5], "cidade": resultado[6], "telefone": resultado[7],
                    "email": resultado[8] }
        else:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")

    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno: {e.__class__.__name__}: {str(e)}")


@empresa_router.post("/upsert")
async def upsert_empresa(empresa: str, db: Session = Depends(get_empresa_db)):
    try:
        sucesso = Insert_Empresa(db, empresa)
        if sucesso:
            return {"message": "Empresa inserida/atualizada com sucesso"}
        else:
            raise HTTPException(status_code=400, detail="Falha ao inserir/atualizar empresa")
    except Exception as e:
        traceback.print_exc()
        enviar_alerta(assunto="Inserção da empresa", mensagem="Erro ao inserir/atualizar empresa: " + str(e))
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")




