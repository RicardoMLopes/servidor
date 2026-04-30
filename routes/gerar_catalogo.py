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

# async def gerar_catalogo_pdf(dados, db):
#     if dados:
#         colunas = ["empresa", "codigo", "descricao", "unidademedida", "codigobarra",
#                    "agrupamento", "marca", "modelo", "tamanho", "cor", "peso",
#                    "precoVenda", "casasdecimais", "percentualdesconto", "estoque", "reajustacondicaopagamento",
#                    "percentualcomissao", "situacaoRegistro", "dataRegistro", "versao", "imagens"]
#
#         produtos = [dict(zip(colunas, item)) for item in dados]
#
#
#     empresa_info = ConsultaEmpresa(db)
#     if not produtos:
#         print("Nenhum produto encontrado.")
#         return
#
#     empresa_nome = empresa_info[1]
#     cnpj = limpa_cnpj(empresa_info[2])
#     endereco = empresa_info[3] if len(empresa_info) > 3 else ""
#     numero = empresa_info[4] if len(empresa_info) > 4 else ""
#     bairro = empresa_info[5] if len(empresa_info) > 5 else ""
#     cidade = empresa_info[6] if len(empresa_info) > 6 else ""
#     telefone = empresa_info[7] if len(empresa_info) > 7 else ""
#     email = empresa_info[8] if len(empresa_info) > 8 else ""
#
#     pasta_destino = os.path.join("static", "img", cnpj)
#     os.makedirs(pasta_destino, exist_ok=True)
#     pasta_temp = os.path.join(pasta_destino, "temp")
#     os.makedirs(pasta_temp, exist_ok=True)
#
#     pdf_path = os.path.join(pasta_destino, "catalogo.pdf")
#     pdf = CatalogoPDF()
#     pdf.set_auto_page_break(auto=True, margin=15)
#     pdf.add_page()
#
#     # Cabeçalho da empresa
#     pdf.set_font("Arial", "B", 16)
#     pdf.cell(0, 10, empresa_nome, ln=True, align="C")
#     pdf.ln(2)
#
#     # Logo da empresa à direita
#     logo_path = localizar_imagem_produto("empresa", pasta_destino)
#     if os.path.isfile(logo_path):
#         pdf.image(logo_path, x=160, y=pdf.get_y() - 15, w=35)
#
#     pdf.set_font("Arial", "", 11)
#     pdf.cell(0, 6, f"Endereço: {endereco}, Nº {numero}", ln=True)
#     pdf.cell(0, 6, f"Cidade: {cidade}", ln=True)
#     pdf.cell(0, 6, f"Bairro: {bairro}", ln=True)
#     pdf.cell(0, 6, f"Telefone: {telefone}", ln=True)
#     pdf.cell(0, 6, f"E-mail: {email}", ln=True)
#     pdf.cell(0, 6, f"CNPJ: {empresa_info[2]}", ln=True)
#
#     # Separador
#     pdf.set_line_width(0.5)
#     pdf.set_draw_color(0, 0, 0)
#     pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
#     pdf.ln(10)
#
#     # Remove duplicidade de produtos
#     produtos_unicos = {}
#     for produto in produtos:
#         codigo = str(produto.get("codigo", "")).strip()
#         if codigo not in produtos_unicos:
#             produtos_unicos[codigo] = produto
#
#     produtos_para_pdf = list(produtos_unicos.values())
#
#     largura_imagem = 35
#     altura_imagem = 35
#     padding_entre = 5
#     espaco_entre_itens = 5
#     largura_texto = 150  # largura para descrição
#
#     itens_por_pagina = [6] + [8] * 20
#     pagina_index = 0
#     itens_na_pagina = 0
#
#     for produto in produtos_para_pdf:
#         # 🔥 calcula altura estimada do item
#         altura_estimada = altura_imagem + 20  # ajuste fino depois se quiser
#
#         # 🔥 verifica se vai estourar a página
#         if pdf.get_y() + altura_estimada > pdf.page_break_trigger:
#             pdf.add_page()
#             itens_na_pagina = 0
#             pagina_index += 1
#
#         if itens_na_pagina >= itens_por_pagina[min(pagina_index, len(itens_por_pagina)-1)]:
#             pdf.add_page()
#             itens_na_pagina = 0
#             pagina_index += 1
#
#         # Localiza e prepara imagem
#         imagem_path = localizar_imagem_produto(str(produto.get("codigo", "")), pasta_destino)
#         try:
#             img = Image.open(imagem_path)
#
#             # 🔥 Corrige transparência e imagens problemáticas
#             if img.mode in ("RGBA", "LA"):
#                 fundo = Image.new("RGB", img.size, (255, 255, 255))
#                 fundo.paste(img, mask=img.split()[-1])
#                 img = fundo
#
#             elif img.mode == "P":
#                 img = img.convert("RGBA")
#                 fundo = Image.new("RGB", img.size, (255, 255, 255))
#                 fundo.paste(img, mask=img.split()[-1])
#                 img = fundo
#
#             else:
#                 img = img.convert("RGB")
#
#             temp_path = os.path.join(pasta_temp, os.path.basename(imagem_path))
#             img.save(temp_path, "JPEG")
#
#             x_img = pdf.get_x()
#             y_img = pdf.get_y()
#             pdf.image(temp_path, x=x_img, y=y_img, w=largura_imagem, h=altura_imagem)
#
#             # Texto do item
#             x_text = x_img + largura_imagem + padding_entre
#             y_text = y_img
#             pdf.set_xy(x_text, y_text)
#             pdf.set_font("Arial", "B", 12)
#             descricao_limpa = limpar_descricao(produto.get('descricao', ''))
#             pdf.multi_cell(largura_texto, 6, f"{produto.get('codigo', '')} - {descricao_limpa}")
#
#             # Agrupamento e código de barra abaixo da descrição
#             y_final_texto = pdf.get_y()
#             pdf.set_xy(x_text, y_final_texto)
#             pdf.set_font("Arial", "", 10)
#             pdf.cell(0, 5, f"Agrupamento: {produto.get('agrupamento', '')}", ln=True)
#             pdf.set_x(x_text)
#             pdf.cell(0, 5, f"Código de Barra: {produto.get('codigobarra', '')}", ln=True)
#
#             # Determina altura máxima entre imagem e texto para posicionar separador
#             altura_max_item = max(y_final_texto + 10 - y_img, altura_imagem)
#             pdf.set_xy(x_img, y_img + altura_max_item + espaco_entre_itens)
#             pdf.set_draw_color(200, 200, 200)
#             pdf.set_line_width(0.3)
#             pdf.line(x_img, pdf.get_y(), 200, pdf.get_y())
#             pdf.ln(espaco_entre_itens)
#
#             # Remove temporário
#             try:
#                 os.remove(temp_path)
#             except OSError:
#                 pass
#
#             itens_na_pagina += 1
#
#         except Exception as e:
#             print(f"Erro ao inserir imagem do produto {produto.get('codigo', '')}: {e}")
#
#     pdf.output(pdf_path)
#     print(f"✅ PDF gerado com sucesso: {os.path.abspath(pdf_path)}")

#---------------------------------------------------------------------------------------------------------------------
# *******************************************************************************************************************
# ====================================================================================================================
import os
import re
import time
from PIL import Image

async def gerar_catalogo_pdf(dados, db):

    import os, re, time
    from PIL import Image
    from io import BytesIO

    start_total = time.time()
    print("\n🚀 ===== INÍCIO GERAÇÃO CATÁLOGO =====")

    try:
        if not dados:
            print("❌ Nenhum produto recebido")
            return

        print(f"📦 Total de registros: {len(dados)}")

        colunas = [
            "empresa", "codigo", "descricao", "unidademedida", "codigobarra",
            "agrupamento", "marca", "modelo", "tamanho", "cor", "peso",
            "precoVenda", "casasdecimais", "percentualdesconto", "estoque",
            "reajustacondicaopagamento", "percentualcomissao",
            "situacaoRegistro", "dataRegistro", "versao", "imagens"
        ]

        produtos = [dict(zip(colunas, item)) for item in dados]

        # =========================
        # EMPRESA
        # =========================
        empresa_info = ConsultaEmpresa(db)

        if not empresa_info:
            print("❌ Empresa não encontrada")
            return

        empresa_nome = empresa_info[1]
        cnpj = limpa_cnpj(empresa_info[2])

        rua = empresa_info[3] or ""
        numero = empresa_info[4] or ""
        bairro = empresa_info[5] or ""
        cidade = empresa_info[6] or ""
        telefone = empresa_info[7] or ""
        email = empresa_info[8] or ""

        # =========================
        # PASTAS
        # =========================
        pasta_destino = os.path.join("static", "img", cnpj)
        pasta_cache = os.path.join(pasta_destino, "cache")

        os.makedirs(pasta_destino, exist_ok=True)
        os.makedirs(pasta_cache, exist_ok=True)

        pdf_path = os.path.join(pasta_destino, "catalogo.pdf")

        # =========================
        # PDF
        # =========================
        pdf = CatalogoPDF()
        pdf.set_auto_page_break(auto=True, margin=10)
        pdf.add_page()

        # =========================
        # CABEÇALHO
        # =========================
        def desenhar_cabecalho():
            try:
                y_top = pdf.get_y()

                logo_path = os.path.join(pasta_destino, f"{cnpj}.png")

                logo_width = 45

                # =========================
                # LOGO (MANTÉM POSIÇÃO ORIGINAL)
                # =========================
                if os.path.exists(logo_path):
                    pdf.image(logo_path, x=10, y=y_top, w=logo_width)
                else:
                    print("⚠️ Logo não encontrada")

                # =========================
                # NOME CENTRALIZADO
                # =========================
                pdf.set_xy(0, y_top)

                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 8, empresa_nome, ln=True, align="C")

                # =========================
                # DADOS CENTRALIZADOS
                # =========================
                pdf.set_font("Arial", "", 10)

                endereco = f"{rua}, {numero} - {bairro} - {cidade}"

                pdf.cell(0, 5, endereco, ln=True, align="C")

                if telefone:
                    pdf.cell(0, 5, f"Tel: {telefone}", ln=True, align="C")

                if email:
                    pdf.cell(0, 5, f"Email: {email}", ln=True, align="C")

                pdf.cell(0, 5, f"CNPJ: {empresa_info[2]}", ln=True, align="C")

                # =========================
                # AJUSTE DE ALTURA (IMPORTANTE)
                # =========================
                # garante que o conteúdo abaixo não sobreponha a logo
                altura_logo = logo_width * 0.6
                if pdf.get_y() < y_top + altura_logo:
                    pdf.set_y(y_top + altura_logo + 5)
                else:
                    pdf.ln(5)

                # =========================
                # LINHA SEPARADORA
                # =========================
                pdf.set_draw_color(200, 200, 200)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(5)

            except Exception as e:
                print(f"❌ Erro cabeçalho: {e}")

        desenhar_cabecalho()

        # =========================
        # CONFIG GRID
        # =========================
        colunas_grid = 2
        itens_por_pagina = 6
        espacamento = 6
        margem = 10

        largura_pagina = 190
        largura_card = (largura_pagina - espacamento) / 2

        img_size = 40
        altura_card = 75

        def sanitize(texto):
            return re.sub(r'[^a-zA-Z0-9_-]', '_', str(texto))

        # =========================
        # FUNÇÃO SEGURA DE IMAGEM
        # =========================
        def abrir_imagem_segura(imagem_path, codigo):

            print(f"📂 [{codigo}] Caminho: {imagem_path}")

            try:
                if not imagem_path:
                    raise Exception("Caminho vazio")

                # BytesIO
                if isinstance(imagem_path, bytes):
                    imagem_path = BytesIO(imagem_path)

                # Caminho inválido
                if isinstance(imagem_path, str) and not os.path.exists(imagem_path):
                    raise Exception("Arquivo não existe")

                img = Image.open(imagem_path)

                # validação real
                img.verify()

                # reabrir após verify
                img = Image.open(imagem_path)

                return img

            except Exception as e:
                print(f"❌ [{codigo}] Imagem inválida: {e}")

                imagem_padrao = os.path.join("static", "img", "sem_imagem.jpg")

                if os.path.exists(imagem_padrao):
                    print(f"🟡 [{codigo}] Usando imagem padrão")
                    return Image.open(imagem_padrao)

                return None

        # =========================
        # LOOP PRODUTOS
        # =========================
        item_index = 0
        coluna = 0
        y_inicio = pdf.get_y()

        for produto in produtos:

            codigo = produto.get("codigo", "SEM_CODIGO")

            try:
                if item_index > 0 and item_index % itens_por_pagina == 0:
                    pdf.add_page()
                    desenhar_cabecalho()
                    coluna = 0
                    y_inicio = pdf.get_y()

                linha = (item_index % itens_por_pagina) // colunas_grid

                x = margem + coluna * (largura_card + espacamento)
                y = y_inicio + linha * altura_card

                codigo_safe = sanitize(codigo)

                imagem_path = localizar_imagem_produto(codigo, pasta_destino)

                img = abrir_imagem_segura(imagem_path, codigo)

                if img is None:
                    continue

                # CACHE
                temp_path = os.path.join(pasta_cache, f"{codigo_safe}.jpg")

                if not os.path.exists(temp_path):

                    if img.mode in ("RGBA", "LA", "P"):
                        fundo = Image.new("RGB", img.size, (255, 255, 255))
                        if img.mode == "P":
                            img = img.convert("RGBA")

                        mask = img.split()[-1] if "A" in img.mode else None
                        fundo.paste(img, mask=mask)
                        img = fundo
                    else:
                        img = img.convert("RGB")

                    img.save(temp_path, "JPEG", quality=85)

                # DESENHO
                pdf.set_xy(x, y)

                img_x = x + (largura_card - img_size) / 2
                pdf.image(temp_path, x=img_x, y=y, w=img_size, h=img_size)

                y_text = y + img_size + 2

                pdf.set_xy(x, y_text)
                pdf.set_font("Arial", "B", 9)

                descricao = limpar_descricao(produto.get('descricao', ''))[:60]

                pdf.multi_cell(
                    largura_card,
                    4,
                    f"{codigo}\n{descricao}",
                    align="C"
                )

                pdf.set_font("Arial", "", 8)
                pdf.set_x(x)
                pdf.cell(largura_card, 4, f"Agr: {produto.get('agrupamento','')}", ln=True, align="C")

                pdf.set_x(x)
                pdf.cell(largura_card, 4, f"CB: {produto.get('codigobarra','')}", ln=True, align="C")

                pdf.line(x, y + altura_card - 2, x + largura_card, y + altura_card - 2)

            except Exception as e:
                print(f"🔥 Erro produto {codigo}: {e}")

            coluna += 1
            if coluna >= colunas_grid:
                coluna = 0

            item_index += 1

        print("\n💾 Salvando PDF...")
        pdf.output(pdf_path)

        print(f"\n✅ PDF gerado: {pdf_path}")
        print(f"⏱️ Tempo total: {round(time.time() - start_total, 2)}s")

    except Exception as e:
        print("\n🔥 ERRO CRÍTICO")
        print(str(e))

# async def gerar_catalogo_pdf(dados, db):
#     if dados:
#         colunas = ["empresa", "codigo", "descricao", "unidademedida", "codigobarra",
#                    "agrupamento", "marca", "modelo", "tamanho", "cor", "peso",
#                    "precoVenda", "casasdecimais", "percentualdesconto", "estoque", "reajustacondicaopagamento",
#                    "percentualcomissao", "situacaoRegistro", "dataRegistro", "versao", "imagens"]
#
#         produtos = [dict(zip(colunas, item)) for item in dados]
#
#     empresa_info = ConsultaEmpresa(db)
#     if not produtos:
#         print("Nenhum produto encontrado.")
#         return
#
#     empresa_nome = empresa_info[1]
#     cnpj = limpa_cnpj(empresa_info[2])
#
#     pasta_destino = os.path.join("static", "img", cnpj)
#     os.makedirs(pasta_destino, exist_ok=True)
#
#     pasta_temp = os.path.join(pasta_destino, "temp")
#     os.makedirs(pasta_temp, exist_ok=True)
#
#     pdf_path = os.path.join(pasta_destino, "catalogo.pdf")
#
#     pdf = CatalogoPDF()
#     pdf.set_auto_page_break(auto=True, margin=15)
#     pdf.add_page()
#
#     # 🔹 Cabeçalho
#     pdf.set_font("Arial", "B", 16)
#     pdf.cell(0, 10, empresa_nome, ln=True, align="C")
#     pdf.ln(5)
#
#     # 🔹 GRID CONFIG
#     colunas_grid = 2
#     largura_pagina = 190
#     margem = 10
#     espacamento = 5
#
#     largura_item = (largura_pagina - (colunas_grid - 1) * espacamento) / colunas_grid
#     altura_imagem = 35
#
#     coluna_atual = 0
#     y_linha = pdf.get_y()
#
#     for produto in produtos:
#
#         if coluna_atual == 0:
#             y_linha = pdf.get_y()
#
#         # 🔥 quebra de página inteligente
#         if pdf.get_y() + 70 > pdf.page_break_trigger:
#             pdf.add_page()
#             coluna_atual = 0
#             y_linha = pdf.get_y()
#
#         x = margem + coluna_atual * (largura_item + espacamento)
#         pdf.set_xy(x, y_linha)
#
#         imagem_path = localizar_imagem_produto(
#             str(produto.get("codigo", "")), pasta_destino
#         )
#
#         try:
#             img = Image.open(imagem_path)
#
#             # 🔥 tratamento de imagem (resolve seu warning)
#             if img.mode in ("RGBA", "LA"):
#                 fundo = Image.new("RGB", img.size, (255, 255, 255))
#                 fundo.paste(img, mask=img.split()[-1])
#                 img = fundo
#             elif img.mode == "P":
#                 img = img.convert("RGBA")
#                 fundo = Image.new("RGB", img.size, (255, 255, 255))
#                 fundo.paste(img, mask=img.split()[-1])
#                 img = fundo
#             else:
#                 img = img.convert("RGB")
#
#             temp_path = os.path.join(pasta_temp, f"{produto.get('codigo')}.jpg")
#             img.save(temp_path, "JPEG")
#
#             # 🔹 IMAGEM CENTRALIZADA
#             pdf.image(
#                 temp_path,
#                 x=x + (largura_item - 30) / 2,
#                 y=pdf.get_y(),
#                 w=30,
#                 h=30
#             )
#
#             pdf.ln(32)
#
#             # 🔹 TEXTO
#             pdf.set_x(x)
#             pdf.set_font("Arial", "B", 9)
#
#             descricao = limpar_descricao(produto.get('descricao', ''))[:80]
#
#             pdf.multi_cell(
#                 largura_item,
#                 4,
#                 f"{produto.get('codigo')} - {descricao}",
#                 align="C"
#             )
#
#             pdf.set_font("Arial", "", 8)
#             pdf.multi_cell(
#                 largura_item,
#                 4,
#                 f"Agr: {produto.get('agrupamento', '')}",
#                 align="C"
#             )
#             pdf.multi_cell(
#                 largura_item,
#                 4,
#                 f"CB: {produto.get('codigobarra', '')}",
#                 align="C"
#             )
#
#             os.remove(temp_path)
#
#         except Exception as e:
#             print(f"Erro ao processar produto {produto.get('codigo')}: {e}")
#
#         coluna_atual += 1
#
#         if coluna_atual >= colunas_grid:
#             coluna_atual = 0
#             pdf.ln(12)
#
#     pdf.output(pdf_path)
#
#     print(f"✅ PDF gerado com sucesso: {os.path.abspath(pdf_path)}")


class CatalogoPDF(FPDF):
    def footer(self):
        # Posição 15 mm da borda inferior
        self.set_y(-15)

        # Linha separadora
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())

        # Fonte menor
        self.set_font("Arial", "I", 8)
        self.set_text_color(100, 100, 100)

        # Texto centralizado
        self.cell(
            0,
            10,
            "Data Access Informática Ltda - Telefone: (31) 3771-8273 - https://dataaccess.inf.br/",
            align="C",
        )