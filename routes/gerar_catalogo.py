import os
from fpdf import FPDF
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

from function.funtions import limpa_cnpj
from database.querys import ConsultaEmpresa

os.makedirs("static", exist_ok=True)
EXTENSOES_VALIDAS = [".JPEG",".PNG",".JPG",".jpg", ".jpeg", ".png", ".webp"]

def sanitizar_codigo(codigo: str) -> str:
    if not codigo:
        return "sem_codigo"
    return "".join(c if c.isalnum() else "_" for c in str(codigo))

def localizar_imagem_produto(codigo_produto: str, pasta_imagens: str) -> str:
    codigo_limpo = sanitizar_codigo(codigo_produto)
    for ext in EXTENSOES_VALIDAS:
        caminho = os.path.join(pasta_imagens, f"{codigo_limpo}{ext}")
        if os.path.isfile(caminho):
            return caminho
    return os.path.join(pasta_imagens, "sem_imagem.jpg")

def limpar_descricao(texto: str) -> str:
    if not texto:
        return ""
    linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]
    return " ".join(linhas)

async def gerar_catalogo_pdf(dados, db):
    if dados:
        colunas = ["empresa", "codigo", "descricao", "unidademedida", "codigobarra",
                   "agrupamento", "marca", "modelo", "tamanho", "cor", "peso",
                   "precoVenda", "casasdecimais", "percentualdesconto", "estoque", "reajustacondicaopagamento",
                   "percentualcomissao", "situacaoRegistro", "dataRegistro", "versao", "imagens"]

        produtos = [dict(zip(colunas, item)) for item in dados]


    empresa_info = ConsultaEmpresa(db)
    if not produtos:
        print("Nenhum produto encontrado.")
        return

    empresa_nome = empresa_info[1]
    cnpj = limpa_cnpj(empresa_info[2])
    endereco = empresa_info[3] if len(empresa_info) > 3 else ""
    numero = empresa_info[4] if len(empresa_info) > 4 else ""
    bairro = empresa_info[5] if len(empresa_info) > 5 else ""
    cidade = empresa_info[6] if len(empresa_info) > 6 else ""
    telefone = empresa_info[7] if len(empresa_info) > 7 else ""
    email = empresa_info[8] if len(empresa_info) > 8 else ""

    pasta_destino = os.path.join("static", "img", cnpj)
    os.makedirs(pasta_destino, exist_ok=True)
    pasta_temp = os.path.join(pasta_destino, "temp")
    os.makedirs(pasta_temp, exist_ok=True)

    pdf_path = os.path.join(pasta_destino, "catalogo.pdf")
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Cabeçalho da empresa
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, empresa_nome, ln=True, align="C")
    pdf.ln(2)

    # Logo da empresa à direita
    logo_path = localizar_imagem_produto("empresa", pasta_destino)
    if os.path.isfile(logo_path):
        pdf.image(logo_path, x=160, y=pdf.get_y() - 15, w=35)

    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 6, f"Endereço: {endereco}, Nº {numero}", ln=True)
    pdf.cell(0, 6, f"Cidade: {cidade}", ln=True)
    pdf.cell(0, 6, f"Bairro: {bairro}", ln=True)
    pdf.cell(0, 6, f"Telefone: {telefone}", ln=True)
    pdf.cell(0, 6, f"E-mail: {email}", ln=True)
    pdf.cell(0, 6, f"CNPJ: {empresa_info[2]}", ln=True)

    # Separador
    pdf.set_line_width(0.5)
    pdf.set_draw_color(0, 0, 0)
    pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
    pdf.ln(10)

    # Remove duplicidade de produtos
    produtos_unicos = {}
    for produto in produtos:
        codigo = str(produto.get("codigo", "")).strip()
        if codigo not in produtos_unicos:
            produtos_unicos[codigo] = produto

    produtos_para_pdf = list(produtos_unicos.values())[:100]

    largura_imagem = 25
    altura_imagem = 25
    padding_entre = 5
    espaco_entre_itens = 5
    largura_texto = 150  # largura para descrição

    itens_por_pagina = [6] + [8] * 20
    pagina_index = 0
    itens_na_pagina = 0

    for produto in produtos_para_pdf:
        if itens_na_pagina >= itens_por_pagina[min(pagina_index, len(itens_por_pagina)-1)]:
            pdf.add_page()
            itens_na_pagina = 0
            pagina_index += 1

        # Localiza e prepara imagem
        imagem_path = localizar_imagem_produto(str(produto.get("codigo", "")), pasta_destino)
        try:
            img = Image.open(imagem_path)
            temp_path = os.path.join(pasta_temp, os.path.basename(imagem_path))
            img.convert("RGB").save(temp_path)

            x_img = pdf.get_x()
            y_img = pdf.get_y()
            pdf.image(temp_path, x=x_img, y=y_img, w=largura_imagem, h=altura_imagem)

            # Texto do item
            x_text = x_img + largura_imagem + padding_entre
            y_text = y_img
            pdf.set_xy(x_text, y_text)
            pdf.set_font("Arial", "B", 12)
            descricao_limpa = limpar_descricao(produto.get('descricao', ''))
            pdf.multi_cell(largura_texto, 6, f"{produto.get('codigo', '')} - {descricao_limpa}")

            # Agrupamento e código de barra abaixo da descrição
            y_final_texto = pdf.get_y()
            pdf.set_xy(x_text, y_final_texto)
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 5, f"Agrupamento: {produto.get('agrupamento', '')}", ln=True)
            pdf.set_x(x_text)
            pdf.cell(0, 5, f"Código de Barra: {produto.get('codigobarra', '')}", ln=True)

            # Determina altura máxima entre imagem e texto para posicionar separador
            altura_max_item = max(y_final_texto + 10 - y_img, altura_imagem)
            pdf.set_xy(x_img, y_img + altura_max_item + espaco_entre_itens)
            pdf.set_draw_color(200, 200, 200)
            pdf.set_line_width(0.3)
            pdf.line(x_img, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(espaco_entre_itens)

            # Remove temporário
            try:
                os.remove(temp_path)
            except OSError:
                pass

            itens_na_pagina += 1

        except Exception as e:
            print(f"Erro ao inserir imagem do produto {produto.get('codigo', '')}: {e}")

    pdf.output(pdf_path)
    print(f"✅ PDF gerado com sucesso: {os.path.abspath(pdf_path)}")
