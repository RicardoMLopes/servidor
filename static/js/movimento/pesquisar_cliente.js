let itensPedido = [];

// 🔹 3. Filtrar Clientes no Modal com Performance Otimizada
let debounceTimerClient = null;

function filtrarClientes(termo) {
    clearTimeout(debounceTimerClient);

    const termoLimpo = termo ? termo.trim() : '';

    if (termoLimpo.length > 0 && termoLimpo.length < 3) {
        document.getElementById('listaClientesResultado').innerHTML = `<tr><td colspan="4" class="text-center text-muted">Digite ao menos 3 caracteres...</td></tr>`;
        return;
    }

    if (termoLimpo.length === 0) {
        document.getElementById('listaClientesResultado').innerHTML = `<tr><td colspan="4" class="text-center text-muted">Digite ao menos 3 caracteres para iniciar a busca...</td></tr>`;
        return;
    }

    debounceTimerClient = setTimeout(() => {
        const token = document.getElementById('token').value;

        fetch(`/novo-pedido/buscar-clientes?token=${token}&termo=${encodeURIComponent(termoLimpo)}`)
            .then(res => res.json())
            .then(data => {
                const tbody = document.getElementById('listaClientesResultado');
                tbody.innerHTML = '';

                if (data.clientes && data.clientes.length > 0) {
                    const fragment = document.createDocumentFragment();

                    data.clientes.forEach(cli => {
                        const tr = document.createElement('tr');

                        tr.innerHTML = `
                            <td>${cli.codigo}</td>
                            <td>${cli.nome}</td>
                            <td>${cli.cpfcnpj || '—'}</td>
                            <td class="text-center">
                                <button type="button" class="btn btn-sm btn-success btn-escolher-cli"
                                    data-codigo="${cli.codigo}"
                                    data-nome="${escapeHtml(cli.nome)}"
                                    data-doc="${cli.cpfcnpj || ''}">
                                    <i class="bi bi-check"></i> Selecionar
                                </button>
                            </td>
                        `;
                        fragment.appendChild(tr);
                    });

                    tbody.appendChild(fragment);
                } else {
                    tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted">Nenhum cliente encontrado.</td></tr>`;
                }
            })
            .catch(err => console.error("Erro ao buscar clientes:", err));
    }, 250);
}

// Função auxiliar para escapar caracteres especiais
function escapeHtml(text) {
    if (!text) return '';
    return text.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// 🔹 4. Gerenciamento Global de Cliques e Eventos do Modal (Blindado contra travamentos)
document.addEventListener('DOMContentLoaded', function () {
    const modalEl = document.getElementById('modalSelecionarCliente');

    if (modalEl) {
        // Evento nativo do Bootstrap disparado quando o modal termina de abrir
        modalEl.addEventListener('shown.bs.modal', function () {
            const inputBusca = document.getElementById('buscaClienteInput');
            if (inputBusca) {
                inputBusca.value = '';
                inputBusca.focus();
            }
            const resultados = document.getElementById('listaClientesResultado');
            if (resultados) {
                resultados.innerHTML = `<tr><td colspan="4" class="text-center text-muted">Digite ao menos 3 caracteres para iniciar a busca...</td></tr>`;
            }
        });

        // Limpeza preventiva e total do backdrop ao fechar
        modalEl.addEventListener('hidden.bs.modal', function () {
            document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
        });
    }
});

// Delegação de evento global para escolher o cliente na tabela do modal
document.addEventListener('click', function(event) {
    const btn = event.target.closest('.btn-escolher-cli');
    if (!btn) return;

    const codigo = btn.getAttribute('data-codigo');
    const nome = btn.getAttribute('data-nome');
    const doc = btn.getAttribute('data-doc');

    selecionarCliente(codigo, nome, doc);
});

function selecionarCliente(codigo, nome, doc) {
    // 1. Atribui os valores aos campos da tela
    document.getElementById('codigocliente').value = codigo;
    document.getElementById('infoClienteDoc').innerText = "CPF/CNPJ: " + (doc || '—');
    document.getElementById('infoClienteNome').innerText = nome;

    // 2. Atualiza o objeto global e o localStorage
    if (typeof window.pedidoAtual !== 'undefined') {
        window.pedidoAtual.codigocliente = codigo;
        window.pedidoAtual.nomecliente = nome;
        window.pedidoAtual.doccliente = "CPF/CNPJ: " + (doc || '—');

        if (typeof salvarEstadoPedido === 'function') {
            salvarEstadoPedido();
        }
    }

    // 🚀 3. DISPARA O POST DIRETAMENTE PARA O BACKEND (Salvar Cabeçalho)
    const tokenElement = document.getElementById('token');
    if (tokenElement && tokenElement.value) {
        const token = tokenElement.value;
        const payload = {
            empresa: window.pedidoAtual?.empresa || 1,
            numerodocumento: window.pedidoAtual?.numerodocumento || null,
            codigocliente: codigo,
            codigovendedor: window.pedidoAtual?.codigovendedor || "001",
            codigocondPagamento: window.pedidoAtual?.codigocondPagamento || "001"
        };

        console.log("🔄 Enviando alteração de cliente para o servidor:", payload);

        fetch(`/novo-pedido/salvar-cabecalho?token=${token}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Se gerou um novo número de documento, atualiza na tela e no objeto global
                if (!window.pedidoAtual.numerodocumento && data.numerodocumento) {
                    window.pedidoAtual.numerodocumento = data.numerodocumento;
                    const displayNum = document.getElementById('displayNumDocumento');
                    if (displayNum) displayNum.innerText = data.numerodocumento;
                    salvarEstadoPedido();
                }
                console.log("✅ Cliente atualizado/salvo com sucesso no banco:", data);
            } else {
                console.error("❌ Erro ao salvar cliente no backend:", data.detail);
            }
        })
        .catch(err => console.error("❌ Erro crítico na requisição de salvamento de cliente:", err));
    }

    // 4. Fecha o modal de forma totalmente segura via API do Bootstrap
    const modalEl = document.getElementById('modalSelecionarCliente');
    if (modalEl) {
        const elementoFocado = modalEl.querySelector(':focus');
        if (elementoFocado) {
            elementoFocado.blur();
        }

        const modalInstance = bootstrap.Modal.getInstance(modalEl);
        if (modalInstance) {
            modalInstance.hide();
        } else {
            const novoModal = new bootstrap.Modal(modalEl);
            novoModal.hide();
        }
    }

    // 5. Força a remoção de qualquer resíduo de backdrop travado na tela
    setTimeout(() => {
        document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    }, 100);
}