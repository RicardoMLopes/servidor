let itensPedido = [];

// 🔹 1. Buscar Produtos por Código ou Código de Barras
function buscarProdutoPorCodigo(codigo) {
    if (!codigo) return;
    const token = document.getElementById('token').value;

    fetch(`/novo-pedido/buscar-produtos?token=${token}&termo=${encodeURIComponent(codigo)}`)
        .then(res => res.json())
        .then(data => {
            if (data.produtos && data.produtos.length > 0) {
                const prod = data.produtos[0];
                document.getElementById('inputCodigo').value = prod.codigo;
                document.getElementById('inputDescricao').value = prod.descricao;
                document.getElementById('inputUnitario').value = prod.precoVenda.toFixed(2);
                document.getElementById('inputQtd').focus();
            } else {
                alert("Produto não encontrado.");
            }
        })
        .catch(err => console.error("Erro ao buscar produto:", err));
}

// 🔹 2. Consultar Produtos pela Descrição
function consultarProdutosDescricao(termo) {
    if (!termo || termo.trim().length < 3) return;

    const token = document.getElementById('token').value;
    fetch(`/novo-pedido/buscar-produtos?token=${token}&termo=${encodeURIComponent(termo)}`)
        .then(res => res.json())
        .then(data => {
            console.log("[LOG PRODUTO] Produtos encontrados:", data.produtos);
        })
        .catch(err => console.error("[LOG PRODUTO] Erro:", err));
}

// 🔹 3. Filtrar Clientes no Modal com Logs
let debounceTimerClient = null;


function filtrarClientes(termo) {
    clearTimeout(debounceTimerClient);

    if (termo && termo.trim().length > 0 && termo.trim().length < 3) {
        document.getElementById('listaClientesResultado').innerHTML = `<tr><td colspan="4" class="text-center text-muted">Digite ao menos 3 caracteres...</td></tr>`;
        return;
    }

    debounceTimerClient = setTimeout(() => {
        const token = document.getElementById('token').value;

        fetch(`/novo-pedido/buscar-clientes?token=${token}&termo=${encodeURIComponent(termo || '')}`)
            .then(res => res.json())
            .then(data => {
                const tbody = document.getElementById('listaClientesResultado');
                tbody.innerHTML = '';

                if (data.clientes && data.clientes.length > 0) {
                    data.clientes.forEach(cli => {
                        const tr = document.createElement('tr');
                        // Tratamento de segurança para evitar erro de aspas no nome do cliente
                        const nomeTratado = cli.nome.replace(/'/g, "\\'").replace(/"/g, '&quot;');

                        tr.innerHTML = `
                            <td>${cli.codigo}</td>
                            <td>${cli.nome}</td>
                            <td>${cli.cpfcnpj}</td>
                            <td class="text-center">
                                <button type="button" class="btn btn-sm btn-success" onclick="selecionarCliente('${cli.codigo}', '${nomeTratado}', '${cli.cpfcnpj}')">
                                    <i class="bi bi-check"></i> Selecionar
                                </button>
                            </td>
                        `;
                        tbody.appendChild(tr);
                    });
                } else {
                    tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted">Nenhum cliente encontrado.</td></tr>`;
                }
            })
            .catch(err => console.error("Erro ao buscar clientes:", err));
    }, 300);
}

function selecionarCliente(codigo, nome, doc) {
    // 1. Atribui os valores aos campos ocultos e visíveis da tela principal
    document.getElementById('codigocliente').value = codigo;
    document.getElementById('infoClienteDoc').innerText = "CPF/CNPJ: " + doc;
    document.getElementById('infoClienteNome').innerText = nome;

    // 2. Fecha o modal de forma segura utilizando a API nativa do Bootstrap 5
    const modalEl = document.getElementById('modalSelecionarCliente');
    let modalInstance = bootstrap.Modal.getInstance(modalEl);

    if (!modalInstance) {
        modalInstance = new bootstrap.Modal(modalEl);
    }
    modalInstance.hide();

    // 3. Remove qualquer resíduo de backdrop (tela cinza travada)
    setTimeout(() => {
        document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    }, 150);
}

// Inicializa o modal limpo sempre que for aberto
document.getElementById('modalSelecionarCliente')?.addEventListener('shown.bs.modal', function () {
    const inputBusca = document.getElementById('buscaClienteInput');
    inputBusca.value = '';
    document.getElementById('listaClientesResultado').innerHTML = `<tr><td colspan="4" class="text-center text-muted">Digite ao menos 3 caracteres para iniciar a busca...</td></tr>`;
    inputBusca.focus();
});

// Evento de abertura do modal
document.getElementById('modalSelecionarCliente')?.addEventListener('shown.bs.modal', function () {
    console.log("[LOG CLIENTE] Modal de clientes foi totalmente aberto (shown).");
    document.getElementById('buscaClienteInput').value = '';
    document.getElementById('listaClientesResultado').innerHTML = `<tr><td colspan="4" class="text-center text-muted">Digite ao menos 3 caracteres para iniciar a busca...</td></tr>`;
    document.getElementById('buscaClienteInput').focus();
});