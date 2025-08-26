from fastapi import APIRouter, Depends, Request, HTTPException
import traceback, json
from model import pedido, schemas_pedido
from typing import List
from sqlalchemy.orm import Session, joinedload
from database.dependencies import get_empresa_db
from params.alerta import enviar_alerta

sincronizar_pedidos = APIRouter()

@sincronizar_pedidos.get("/", response_model=List[schemas_pedido.PedidoSchema])
def listar_pedidos(request: Request, db: Session = Depends(get_empresa_db)):
    try:
        # Carrega pedidos com itens
        pedidos = db.query(pedido.MovNota)\
            .options(joinedload(pedido.MovNota.itens))\
            .filter(pedido.MovNota.status == "P")\
            .all()

        print(f"Pedidos encontrados: {len(pedidos)}")
        for p in pedidos:
            print(f"Pedido {p.numerodocumento} - Itens: {len(p.itens)}")

        # Se tudo certo, atualiza status para 'R'
        for p in pedidos:
            p.status = "R"
        db.commit()  # aplica as alterações no banco

        return pedidos

    except Exception as e:
        traceback.print_exc()

        # Serializa pedidos em JSON para envio por e-mail
        try:
            pedidos_json = json.dumps(
                [schemas_pedido.PedidoSchema.from_orm(p).dict() for p in pedidos],
                indent=2
            )
        except Exception as ex:
            pedidos_json = f"Erro ao gerar JSON: {ex}"

        # Envia alerta com o JSON completo como anexo
        enviar_alerta(
            assunto='Erro de sincronização de pedidos',
            mensagem=f'Erro: {str(e)}',
            anexo={'nome_arquivo': 'pedidos_erro.json', 'conteudo': pedidos_json}
        )
        raise HTTPException(status_code=500, detail=f"Erro ao listar pedidos: {str(e)}")
