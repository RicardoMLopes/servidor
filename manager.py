from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from routes import parameter_router
from routes.cadusers import cadusers_router
from routes.produto import products_router
from routes.empresa import empresa_router
from routes.sicronizeimage import imagem_router
from routes.vendedor import vendedor_router
from routes.cliente import cliente_router
from routes.formaparameto import condicao_pagamento_router
from funtions import templates



app = FastAPI()

# Rota arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")




# Registrando os routers
app.include_router(imagem_router, prefix="/lista", tags=["Imagem"])
app.include_router(empresa_router, prefix="/empresa", tags=["Empresa"])
app.include_router(products_router, prefix="/produtos", tags=["Produtos"])
app.include_router(parameter_router, prefix="/parametro", tags=["Parametro"])
app.include_router(vendedor_router, prefix="/vendedores", tags=["Vendedor"])
app.include_router(cliente_router, prefix="/clientes" ,tags=["Cliente"])
app.include_router(condicao_pagamento_router, prefix="/condicoespagamento", tags=["Condicao"])
app.include_router(cadusers_router, prefix="/cadusuarios", tags=["Cadusuario"])
app.include_router(cadusers_router)








