let debounceTimerProduto = null;

// 🔹 Utilitário para escapar caracteres especiais nas propriedades HTML
function escapeHtml(texto) {
    if (!texto) return '';
    return String(texto)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// 🔹 Utilitário para formatar código de produto com Zeros à Esquerda (ex: 23 -> 00023)
function formatarCodigoProduto(codigo) {
    if (!codigo) return '';
    const codigoLimpo = String(codigo).trim();
    // Se for numérico, preenche com zeros à esquerda até completar 5 dígitos
    if (/^\d+$/.test(codigoLimpo)) {
        return codigoLimpo.padStart(5, '0');
    }
    return codigoLimpo;
}

// 🔹 1. Inicialização segura dos modais e eventos da página
document.addEventListener('DOMContentLoaded', function () {
    const modalProdutoEl = document.getElementById('modalSelecionarProduto');
    const btnAbrirModal = document.getElementById('btnAbrirModalProduto');

    if (modalProdutoEl && btnAbrirModal) {
        // Instancia o modal de forma limpa via JS (evita conflitos e bugs de backdrop)
        const modalProduto = new bootstrap.Modal(modalProdutoEl);

        btnAbrirModal.addEventListener('click', function (e) {
            e.preventDefault();
            modalProduto.show();
        });

        // Evento disparado quando o modal termina de abrir
        modalProdutoEl.addEventListener('shown.bs.modal', function () {
            const inputBusca = document.getElementById('buscaProdutoInput');
            if (inputBusca) {
                inputBusca.value = '';
                inputBusca.focus();
            }
            const resultados = document.getElementById('listaProdutosResultado');
            if (resultados) {
                resultados.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-4"><i class="bi bi-info-circle me-1"></i> Digite ao menos 3 caracteres para iniciar a busca...</td></tr>`;
            }
        });

        // Garantia de limpeza ao fechar o modal
        modalProdutoEl.addEventListener('hidden.bs.modal', function () {
            document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
        });
    }

    // 🔹 Evento ao sair do campo de código manual (blur/enter) para aplicar o padStart
    const inputCodigo = document.getElementById('inputCodigo');
    if (inputCodigo) {
        inputCodigo.addEventListener('blur', function () {
            if (this.value) {
                this.value = formatarCodigoProduto(this.value);
            }
        });
    }
});

// 🔹 2. Função para buscar produtos dinamicamente dentro do Modal
function filtrarProdutosModal(termo) {
    clearTimeout(debounceTimerProduto);
    const termoLimpo = termo ? termo.trim() : '';

    if (termoLimpo.length > 0 && termoLimpo.length < 3) {
        document.getElementById('listaProdutosResultado').innerHTML = `<tr><td colspan="5" class="text-center text-muted py-4"><i class="bi bi-exclamation-circle me-1"></i> Digite ao menos 3 caracteres...</td></tr>`;
        return;
    }

    if (termoLimpo.length === 0) {
        document.getElementById('listaProdutosResultado').innerHTML = `<tr><td colspan="5" class="text-center text-muted py-4"><i class="bi bi-info-circle me-1"></i> Digite ao menos 3 caracteres para iniciar a busca...</td></tr>`;
        return;
    }

    debounceTimerProduto = setTimeout(() => {
        const tokenElement = document.getElementById('token');
        if (!tokenElement) return;
        const token = tokenElement.value;

        // 🔹 Captura a Condição de Pagamento selecionada no formulário/estado
        const condPagamento = document.getElementById('codigocondPagamento')?.value ||
                              window.pedidoAtual?.codigocondPagamento || '';

        // 🔹 Inclui o codigocondPagamento na URL do fetch
        fetch(`/novo-pedido/buscar-produtos?token=${token}&termo=${encodeURIComponent(termoLimpo)}&codigocondPagamento=${encodeURIComponent(condPagamento)}`)
            .then(res => res.json())
            .then(data => {
                const tbody = document.getElementById('listaProdutosResultado');
                tbody.innerHTML = '';

                if (data.produtos && data.produtos.length > 0) {
                    const fragment = document.createDocumentFragment();

                    data.produtos.forEach(prod => {
                        // Formata o código do produto para 5 dígitos
                        const codigoFormatado = formatarCodigoProduto(prod.codigo);

                        // 🔹 GARANTE A CONVERSÃO PARA FLOAT AQUI
                        const precoCalculado = parseFloat(prod.valorUnitario ?? prod.precoVenda ?? prod.preco ?? 0);
                        const precoOriginal = parseFloat(prod.precoVenda ?? prod.valorUnitario ?? prod.preco ?? 0);

                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td class="fw-semibold text-secondary">${codigoFormatado}</td>
                            <td><span class="badge bg-light text-dark border">${prod.codigobarra || '—'}</span></td>
                            <td class="fw-bold text-dark">${prod.descricao}</td>
                            <td class="text-end fw-semibold text-success">R$ ${precoCalculado.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                            <td class="text-center">
                                <button type="button" class="btn btn-sm btn-primary rounded-pill px-3 fw-semibold btn-escolher-prod shadow-sm text-nowrap"
                                    data-codigo="${codigoFormatado}"
                                    data-descricao="${escapeHtml(prod.descricao)}"
                                    data-preco="${precoCalculado}"
                                    data-preco-venda-original="${precoOriginal}">
                                    <i class="bi bi-check2 me-1"></i> Selecionar
                                </button>
                            </td>
                        `;
                        fragment.appendChild(tr);
                    });

                    tbody.appendChild(fragment);
                } else {
                    tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-4"><i class="bi bi-search me-1"></i> Nenhum produto encontrado.</td></tr>`;
                }
            })
            .catch(err => console.error("Erro ao buscar produtos:", err));
    }, 250);
}

// 🔹 3. Delegação de evento global para escolher o produto direto da tabela do modal
document.addEventListener('click', function(event) {
    const btn = event.target.closest('.btn-escolher-prod');
    if (!btn) return;

    const codigo = btn.getAttribute('data-codigo');
    const descricao = btn.getAttribute('data-descricao');
    const preco = parseFloat(btn.getAttribute('data-preco'));

    // Captura o preço base de tabela (se não existir, usa o próprio preço calculado)
    const precoOriginalAttr = btn.getAttribute('data-preco-venda-original');
    const precoOriginal = precoOriginalAttr ? parseFloat(precoOriginalAttr) : preco;

    preencherProdutoSelecionado(codigo, descricao, preco, precoOriginal);
});

/// 🔹 Função para buscar o produto pelo código digitado manualmente (usando a rota unificada)
async function buscarProdutoPorCodigo(codigoInput) {
    if (!codigoInput || codigoInput.trim() === "") return;

    const codigo = formatarCodigoProduto(codigoInput);

    const inputCodigoEl = document.getElementById('inputCodigo');
    if (inputCodigoEl) inputCodigoEl.value = codigo;

    const tokenElement = document.getElementById('token');
    if (!tokenElement) return;
    const token = tokenElement.value;

    const condPagamento = document.getElementById('codigocondPagamento')?.value ||
                          window.pedidoAtual?.codigocondPagamento || '';

    try {
        // 🔹 Aponta para a mesma rota /buscar-produtos enviando no parâmetro 'termo'
        const url = `/novo-pedido/buscar-produtos?token=${token}&termo=${encodeURIComponent(codigo)}&codigocondPagamento=${encodeURIComponent(condPagamento)}`;
        const response = await fetch(url);
        const data = await response.json();

        // Como a rota retorna um array {"produtos": [...]}, pegamos o primeiro resultado encontrado
        if (data && data.produtos && data.produtos.length > 0) {
            const produto = data.produtos[0];

            // Preenche a descrição
            const campoDesc = document.getElementById('inputDescricao');
            if (campoDesc) campoDesc.value = produto.descricao || '';

            // Preenche os valores
            const inputUnitario = document.getElementById('inputUnitario');
            if (inputUnitario) {
                inputUnitario.value = parseFloat(produto.valorUnitario).toFixed(2);
                inputUnitario.dataset.precoVendaOriginal = parseFloat(produto.precoVenda).toFixed(2);
            }

            // Foca na quantidade
            const inputQtd = document.getElementById('inputQtd');
            if (inputQtd) {
                inputQtd.focus();
                inputQtd.select();
            }
        } else {
            await mostrarModal({
                titulo: "Atenção",
                mensagem: `Produto com o código "${codigo}" não foi encontrado.`,
                botoes: [{ texto: "OK", valor: true, classe: "btn-primary" }]
            });

            limparCamposProduto();
        }
    } catch (err) {
        console.error("Erro na busca do produto:", err);
        limparCamposProduto();
    }
}

function limparCamposProduto() {
    document.getElementById('inputCodigo').value = '';
    document.getElementById('inputDescricao').value = '';
    document.getElementById('inputUnitario').value = '0.00';
    document.getElementById('inputCodigo').focus();
}

// 🔹 4. Preenche os campos do formulário e fecha o modal de produtos com segurança
function preencherProdutoSelecionado(codigo, descricao, preco, precoOriginal = null) {
    // Garante que o código preenchido no input tenha 5 dígitos
    const codigoFormatado = formatarCodigoProduto(codigo);

    document.getElementById('inputCodigo').value = codigoFormatado;
    document.getElementById('inputDescricao').value = descricao;

    // Preenche o preço unitário (calculado) e armazena o original no dataset
    const inputUnitario = document.getElementById('inputUnitario');
    if (inputUnitario) {
        const precoCalculadoNum = parseFloat(preco) || 0;
        const precoOriginalNum = precoOriginal !== null ? parseFloat(precoOriginal) : precoCalculadoNum;

        inputUnitario.value = precoCalculadoNum.toFixed(2);
        inputUnitario.dataset.precoVendaOriginal = precoOriginalNum.toFixed(2);
    }

    // Foca na quantidade e seleciona o texto para agilizar a digitação
    const inputQtd = document.getElementById('inputQtd');
    if (inputQtd) {
        inputQtd.focus();
        inputQtd.select();
    }

    // Fecha o modal de produtos via API nativa do Bootstrap
    const modalEl = document.getElementById('modalSelecionarProduto');
    if (modalEl) {
        const elementoFocado = modalEl.querySelector(':focus');
        if (elementoFocado) {
            elementoFocado.blur();
        }

        const modalInstance = bootstrap.Modal.getInstance(modalEl);
        if (modalInstance) {
            modalInstance.hide();
        }
    }

    // 🔹 BUSCA ANTECIPADA DO LIMITE DE DESCONTO DO PRODUTO/VENDEDOR
    const token = document.getElementById('token')?.value || '';
    const codigoVendedor = window.pedidoAtual?.codigovendedor || "001";

    if (token && codigoFormatado && codigoVendedor) {
        fetch(`/novo-pedido/limite-desconto?token=${token}&codigovendedor=${codigoVendedor}&codigoproduto=${codigoFormatado}`)
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    window.limiteDescontoItemAtual = data.limiteMaximoPercentual;
                    console.log(`✅ Limite de desconto pré-carregado para o produto ${codigoFormatado}: ${window.limiteDescontoItemAtual}%`);
                }
            })
            .catch(err => console.error("⚠️ Erro ao pré-carregar limite de desconto:", err));
    }
}