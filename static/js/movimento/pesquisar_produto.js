let debounceTimerProduto = null;

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
        const token = document.getElementById('token').value;

        fetch(`/novo-pedido/buscar-produtos?token=${token}&termo=${encodeURIComponent(termoLimpo)}`)
            .then(res => res.json())
            .then(data => {
                const tbody = document.getElementById('listaProdutosResultado');
                tbody.innerHTML = '';

                if (data.produtos && data.produtos.length > 0) {
                    const fragment = document.createDocumentFragment();

                    data.produtos.forEach(prod => {
                        const tr = document.createElement('tr');
                            tr.innerHTML = `
                                <td class="fw-semibold text-secondary">${prod.codigo}</td>
                                <td><span class="badge bg-light text-dark border">${prod.codigobarra || '—'}</span></td>
                                <td class="fw-bold text-dark">${prod.descricao}</td>
                                <td class="text-end fw-semibold text-success">R$ ${prod.precoVenda.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</td>
                                <td class="text-center">
                                    <!-- Removida qualquer classe de largura estendida e mantido o botão compacto -->
                                    <button type="button" class="btn btn-sm btn-primary rounded-pill px-3 fw-semibold btn-escolher-prod shadow-sm text-nowrap"
                                        data-codigo="${prod.codigo}"
                                        data-descricao="${escapeHtml(prod.descricao)}"
                                        data-preco="${prod.precoVenda}">
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

    preencherProdutoSelecionado(codigo, descricao, preco);
});

// 🔹 Função para buscar o produto pelo código digitado manualmente
async function buscarProdutoPorCodigo(codigo) {
    if (!codigo || codigo.trim() === "") return;

    const tokenElement = document.getElementById('token');
    if (!tokenElement) {
        console.error("Token não encontrado na tela.");
        return;
    }
    const token = tokenElement.value;

    console.log("🔍 Buscando produto pelo código:", codigo);

    try {
        const response = await fetch(`/novo-pedido/buscar-produto?token=${token}&codigo=${encodeURIComponent(codigo)}`);
        const data = await response.json();

        // Verifica se o produto foi retornado com sucesso
        if (data && (data.success || data.encontrado || data.descricao || data.descricaoproduto)) {
            // Preenche a descrição
            const campoDesc = document.getElementById('inputDescricao');
            if (campoDesc) {
                campoDesc.value = data.descricao || data.descricaoproduto || '';
            }

            // Preenche o valor unitário
            const inputUnitario = document.getElementById('inputUnitario');
            if (inputUnitario) {
                const preco = data.precoVenda || data.valorUnitario || data.preco || 0;
                inputUnitario.value = parseFloat(preco).toFixed(2);
            }

            // Joga o foco direto para a quantidade
            const inputQtd = document.getElementById('inputQtd');
            if (inputQtd) {
                inputQtd.focus();
                inputQtd.select();
            }
        } else {
            // ❌ Modal de alerta quando o produto não é encontrado
            await mostrarModal({
                titulo: "Atenção",
                mensagem: `Produto com o código "${codigo}" não foi encontrado.`,
                botoes: [{ texto: "OK", valor: true, classe: "btn-primary" }]
            });

            limparCamposProduto();
        }
    } catch (err) {
        console.error("Erro na busca do produto:", err);

        // ❌ Modal de erro no servidor
        await mostrarModal({
            titulo: "Erro do Servidor",
            mensagem: "Não foi possível consultar o produto no servidor. Tente novamente.",
            botoes: [{ texto: "Entendido", valor: false, classe: "btn-danger" }]
        });

        document.getElementById('inputCodigo').value = '';
        document.getElementById('inputCodigo').focus();
    }
}

function limparCamposProduto() {
    document.getElementById('inputCodigo').value = '';
    document.getElementById('inputDescricao').value = '';
    document.getElementById('inputUnitario').value = '0.00';
    document.getElementById('inputCodigo').focus();
}

// 🔹 4. Preenche os campos do formulário e fecha o modal de produtos com segurança
function preencherProdutoSelecionado(codigo, descricao, preco) {
    document.getElementById('inputCodigo').value = codigo;
    document.getElementById('inputDescricao').value = descricao;
    document.getElementById('inputUnitario').value = preco.toFixed(2);

    // Foca na quantidade e seleciona o texto para agilizar a digitação
    const inputQtd = document.getElementById('inputQtd');
    if (inputQtd) {
        inputQtd.focus();
        inputQtd.select();
    }

    // Fecha o modal de produtos via API nativa do Bootstrap
    const modalEl = document.getElementById('modalSelecionarProduto');
    if (modalEl) {
        // Remove o foco de qualquer elemento dentro do modal antes de fechá-lo
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

    if (token && codigo && codigoVendedor) {
        fetch(`/novo-pedido/limite-desconto?token=${token}&codigovendedor=${codigoVendedor}&codigoproduto=${codigo}`)
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    // Armazena globalmente o limite para este item selecionado
                    window.limiteDescontoItemAtual = data.limiteMaximoPercentual;
                    console.log(`✅ Limite de desconto pré-carregado para o produto ${codigo}: ${window.limiteDescontoItemAtual}%`);
                }
            })
            .catch(err => console.error("⚠️ Erro ao pré-carregar limite de desconto:", err));
    }
}