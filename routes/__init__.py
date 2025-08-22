from .empresa import empresa_router
from .produto import products_router
from .sicronizeimage import imagem_router
from .parametro import parameter_router
from .vendedor import vendedor_router
from .cliente import cliente_router
from .formaparameto import condicao_pagamento_router
from .cadusers import cadusers_router
from .cadusers import sincronizaruser_router, recuperaruser_router
from .pedidovenda import pedido_router
from .sincronizarpedido import sincronizar_pedidos

__all__ = [
            "empresa_router", "products_router", "imagem_router", "parameter_router", "vendedor_router",
            "cliente_router", "condicao_pagamento_router", "cadusers_router", "sincronizaruser_router",
            "recuperaruser_router", "pedido_router", "sincronizar_pedidos",
           ]
