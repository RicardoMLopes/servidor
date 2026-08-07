from decimal import Decimal



def calcular_desconto(
    valor,
    tipo,
    desconto
):

    desconto = Decimal(desconto)


    if tipo == "P":

        return valor * desconto / 100


    return desconto




def calcular_acrescimo(
    valor,
    tipo,
    acrescimo
):

    acrescimo = Decimal(acrescimo)


    if tipo == "P":

        return valor * acrescimo / 100


    return acrescimo





def calcular_total_pedido(
    subtotal,
    tipo_desconto,
    desconto,
    tipo_acrescimo,
    acrescimo
):


    valor_desconto = calcular_desconto(
        subtotal,
        tipo_desconto,
        desconto
    )


    valor_acrescimo = calcular_acrescimo(
        subtotal,
        tipo_acrescimo,
        acrescimo
    )


    total = (
        subtotal
        - valor_desconto
        + valor_acrescimo
    )


    return {

        "subtotal": subtotal,

        "desconto": valor_desconto,

        "acrescimo": valor_acrescimo,

        "total": total

    }