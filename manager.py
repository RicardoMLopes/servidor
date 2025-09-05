import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
# from starlette.responses import HTMLResponse
# from routes.gerar_catalogo_diario import gerar_catalogo_diario
from routes import parameter_router, sincronizaruser_router, pedido_router, alterarsenha_router, email_router, \
    home_router, list_products_router
from routes.cadusers import cadusers_router
from routes.pedidovenda import pedido_relatorios_router, pedido_router, pedido_relatorios_PDF_router
from routes.recuperar_password import recuperaruser_router
from routes.gerar_catalogo_diario import gerar_catalogo_diario
from routes.produto import products_router
from routes.empresa import empresa_router
from routes.sicronizeimage import imagem_router
from routes.vendedor import vendedor_router
from routes.cliente import cliente_router
from routes.formaparameto import condicao_pagamento_router
from routes.sincronizarpedido import sincronizar_pedidos
# from fastapi.middleware.wsgi import WSGIMiddleware
# from markupsafe import escape

app = FastAPI()

gerar_catalogo_diario()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rota arquivos estáticos
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.on_event("startup")
async def startup_event():
    # Gera catálogo diário assim que o app inicia
    asyncio.create_task(gerar_catalogo_diario())

# Registrando os routers
app.include_router(home_router, prefix="", tags=["home"])
app.include_router(home_router, prefix="/identificar-empresa", tags=["home"])
app.include_router(home_router, prefix="/dashboard", tags=["home"])
app.include_router(home_router, prefix="/cadastrar-users", tags=["home"])
app.include_router(home_router, prefix="/image", tags=["Imagem"])



# IMAGEM
app.include_router(imagem_router, prefix="/lista", tags=["Imagem"])

# EMPRESA
app.include_router(empresa_router, prefix="/empresa", tags=["Empresa"])

# PRODUTO
app.include_router(products_router, prefix="/produtos", tags=["Produtos"])
app.include_router(list_products_router, prefix="/listar-produtos", tags=["Produtos"])
app.include_router(products_router, prefix="/insert-produtos", tags=["Produtos"])

# PARAMETRO
app.include_router(parameter_router, prefix="/parametro", tags=["Parametro"])

# VENDEDOR
app.include_router(vendedor_router, prefix="/vendedores", tags=["Vendedor"])

# CLIENTE
app.include_router(cliente_router, prefix="/clientes" ,tags=["Cliente"])
app.include_router(cliente_router, prefix="/insert-clientes" ,tags=["Cliente"])

# FORMA DE PAGAMENTO
app.include_router(condicao_pagamento_router, prefix="/condicoespagamento", tags=["Condicao"])

# USUÁRIO
app.include_router(cadusers_router, prefix="/cadusuarios", tags=["Cadusuario"])
app.include_router(alterarsenha_router, prefix="/alterar-senha", tags=["Alterarsenha"])
app.include_router(sincronizaruser_router, prefix="/sincronizausers", tags=["users"])
app.include_router(recuperaruser_router, prefix="/recuperar-senha", tags=["Recuperar"])
app.include_router(recuperaruser_router, prefix="/esqueci-senha", tags=["Recuperar"])
app.include_router(alterarsenha_router, prefix="/buscar-usuario-vendedor", tags=["Recuperar"])
app.include_router(cadusers_router)

# PEDIDO DE VENDA
app.include_router(pedido_router, prefix="/pedidos", tags=["Pedido"])
app.include_router(pedido_relatorios_router, prefix="/pedido-relatorios", tags=["Pedido Relatório"])
app.include_router(pedido_relatorios_PDF_router, prefix="/pedido-relatorios-pdf", tags=["Pedido PDF"])
app.include_router(sincronizar_pedidos, prefix="/sincronizarpedidos",tags=["Sincronizar Pedidos"])

# E-MAIL
app.include_router(email_router, prefix="/enviar-email", tags=["Email"])
