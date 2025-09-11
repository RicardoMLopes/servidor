from datetime import datetime
from decimal import Decimal

def serializar_relatorio(relatorio):
    """
    Converte o relatório em formato JSON-serializável.
    Transforma datas em string ISO, Decimals em float e valores nulos em 0.
    """
    relatorio_serializable = []

    for p in relatorio:
        cab = getattr(p, "cabecalho", {})
        itens_serializados = []
        for i in getattr(p, "itens", []) or []:
            itens_serializados.append({
                "codigoproduto": getattr(i, "codigoproduto", ""),
                "descricaoproduto": getattr(i, "descricaoproduto", ""),
                "quantidade": float(getattr(i, "quantidade", 0) or 0),
                "valorunitariovenda": float(getattr(i, "valorunitariovenda", 0) or 0),
                "valorDesconto": float(getattr(i, "valorDesconto", 0) or 0),
                "valoracrescimo": float(getattr(i, "valoracrescimo", 0) or 0),
                "valorTotal": float(getattr(i, "valorTotal", 0) or 0),
                "unidadeMedida": getattr(i, "unidadeMedida", "")
            })

        totals = getattr(p, "totalizadores", {})
        relatorio_serializable.append({
            "cabecalho": {
                "numerodocumento": getattr(cab, "numerodocumento", ""),
                "codigovendedor": getattr(cab, "codigovendedor", ""),
                "nomevendedor": getattr(cab, "nomevendedor", ""),
                "codigocliente": getattr(cab, "codigocliente", ""),
                "nomecliente": getattr(cab, "nomecliente", ""),
                "dataLancamento": getattr(cab, "dataLancamento", "").isoformat()
                                  if isinstance(getattr(cab, "dataLancamento", None), datetime)
                                  else getattr(cab, "dataLancamento", ""),
                "codigocondPagamento": getattr(cab, "codigocondPagamento", ""),
                "formapagamento": getattr(cab, "formapagamento", ""),
                "status": getattr(cab, "status", "")
            },
            "itens": itens_serializados,
            "totalizadores": {
                "subtotal": float(getattr(totals, "subtotal", 0) or 0),
                "totalDesconto": float(getattr(totals, "totalDesconto", 0) or 0),
                "totalAcrescimo": float(getattr(totals, "totalAcrescimo", 0) or 0),
                "totalGeral": float(getattr(totals, "totalGeral", 0) or 0)
            }
        })

    return relatorio_serializable
