import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
from starlette.responses import HTMLResponse
from routes.gerar_catalogo_diario import gerar_catalogo_diario
from routes import parameter_router, sincronizaruser_router, recuperaruser_router, pedido_router
from routes.cadusers import cadusers_router
from routes.gerar_catalogo_diario import gerar_catalogo_diario
from routes.produto import products_router
from routes.empresa import empresa_router
from routes.sicronizeimage import imagem_router
from routes.vendedor import vendedor_router
from routes.cliente import cliente_router
from routes.formaparameto import condicao_pagamento_router
# from fastapi.middleware.wsgi import WSGIMiddleware
# from markupsafe import escape
from funtions import templates

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
app.include_router(imagem_router, prefix="/lista", tags=["Imagem"])
app.include_router(empresa_router, prefix="/empresa", tags=["Empresa"])
app.include_router(products_router, prefix="/produtos", tags=["Produtos"])
app.include_router(parameter_router, prefix="/parametro", tags=["Parametro"])
app.include_router(vendedor_router, prefix="/vendedores", tags=["Vendedor"])
app.include_router(cliente_router, prefix="/clientes" ,tags=["Cliente"])
app.include_router(condicao_pagamento_router, prefix="/condicoespagamento", tags=["Condicao"])
app.include_router(cadusers_router, prefix="/cadusuarios", tags=["Cadusuario"])
app.include_router(sincronizaruser_router, prefix="/sincronizausers", tags=["users"])
app.include_router(recuperaruser_router, prefix="/recuperar-senha", tags=["Recuperar"])
app.include_router(recuperaruser_router, prefix="/buscar-usuario-vendedor", tags=["Recuperar"])
app.include_router(pedido_router, prefix="/pedidos", tags=["Pedido"])
app.include_router(cadusers_router)