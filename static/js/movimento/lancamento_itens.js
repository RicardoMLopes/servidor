// 🔹 Inicializa o pedido global utilizando os dados injetados pelo backend no template HTML (suporte nativo ao F5 via Banco de Dados)
if (typeof window.pedidoAtual === 'undefined') {
    window.pedidoAtual = {
        empresa: 1,
        numerodocumento: null,
        codigovendedor: "001",
        codigocliente: "00001",
        codigocondPagamento: "001"
    };
}

// 🔹 Função auxiliar para opcionalmente salvar no localStorage como cache secundário
function salvarEstadoPedido() {
    const elNome = document.getElementById('infoClienteNome');
    const elDoc = document.getElementById('infoClienteDoc');

    const inputEmpresa = document.getElementById('empresa');
    const inputVendedor = document.getElementById('codigovendedor');
    const inputCliente = document.getElementById('codigocliente');
    const inputCondPag = document.getElementById('codigocondPagamento');

    if (inputEmpresa) window.pedidoAtual.empresa = inputEmpresa.value;
    if (inputVendedor) window.pedidoAtual.codigovendedor = inputVendedor.value;
    if (inputCliente) window.pedidoAtual.codigocliente = inputCliente.value;
    if (inputCondPag) window.pedidoAtual.codigocondPagamento = inputCondPag.value;

    if (elNome) window.pedidoAtual.nomecliente = elNome.innerText;
    if (elDoc) window.pedidoAtual.doccliente = elDoc.innerText;

    localStorage.setItem('pedidoEmAndamento', JSON.stringify(window.pedidoAtual));
}

// 🔹 Ao carregar a página (F5 ou acesso inicial), se já houver um documento em andamento, carrega os itens automaticamente
document.addEventListener('DOMContentLoaded', () => {
    if (window.pedidoAtual.numerodocumento) {
        console.log("Restaurando pedido anterior após F5:", window.pedidoAtual.numerodocumento);
        if (typeof carregarItensPedido === 'function') {
            carregarItensPedido();
        }
    }
});

// 🔹 Função para adicionar um item na tabela e gravar no backend
function adicionarItemNaTabela() {
    const tokenElement = document.getElementById('token');
    if (!tokenElement) {
        alert("Token da empresa não encontrado na tela.");
        return;
    }
    const token = tokenElement.value;

    const codigo = document.getElementById('inputCodigo').value;
    const descricao = document.getElementById('inputDescricao').value;
    const quantidade = parseFloat(document.getElementById('inputQtd').value) || 0;
    const valorUnitario = parseFloat(document.getElementById('inputUnitario').value) || 0;

    // 🔹 Captura o código do cliente atual direto do input oculto da tela, garantindo que não envie o desatualizado
    const inputCodCliente = document.getElementById('inputCodigoCliente');
    if (inputCodCliente && inputCodCliente.value) {
        window.pedidoAtual.codigocliente = inputCodCliente.value;
    }

    if (!codigo || quantidade <= 0 || valorUnitario <= 0) {
        alert("Informe um produto válido, quantidade e valor unitário maiores que zero.");
        return;
    }

    const payload = {
        empresa: window.pedidoAtual.empresa,
        numerodocumento: window.pedidoAtual.numerodocumento,
        codigovendedor: window.pedidoAtual.codigovendedor,
        codigocliente: window.pedidoAtual.codigocliente,
        codigocondPagamento: window.pedidoAtual.codigocondPagamento,
        item: {
            codigoproduto: codigo,
            descricaoproduto: descricao,
            quantidade: quantidade,
            valorUnitario: valorUnitario,
            valorDesconto: window.itemEmEdicaoDescontoAcrescimo?.valorDesconto || 0,
            valoracrescimo: window.itemEmEdicaoDescontoAcrescimo?.valoracrescimo || 0
        }
    };

    fetch(`/novo-pedido/adicionar-item?token=${token}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            // Atualiza as chaves globais com o número do documento gerado/atualizado pelo backend
            window.pedidoAtual.empresa = data.empresa;
            window.pedidoAtual.numerodocumento = data.numerodocumento;
            window.pedidoAtual.codigocliente = data.codigocliente;
            window.pedidoAtual.codigovendedor = data.codigovendedor;
            window.pedidoAtual.codigocondPagamento = data.codigocondPagamento;

            // Salva o estado atualizado no navegador (cache)
            salvarEstadoPedido();

            // 🔹 Reseta o cache temporário de desconto/acréscimo do item recém-adicionado
            window.itemEmEdicaoDescontoAcrescimo = null;

            // Limpa os campos do produto para o próximo lançamento
            document.getElementById('inputCodigo').value = '';
            document.getElementById('inputDescricao').value = '';
            document.getElementById('inputQtd').value = '1';
            document.getElementById('inputUnitario').value = '0.00';
            document.getElementById('inputCodigo').focus();

            // Atualiza a tabela na tela
            if (typeof carregarItensPedido === 'function') {
                carregarItensPedido();
            }
        } else {
            alert("Erro ao gravar item: " + (data.detail || "Erro desconhecido"));
        }
    })
    .catch(err => console.error("Erro na requisição de adição de item:", err));
}

// 🔹 Função para carregar e listar os itens do pedido na tabela HTML
function carregarItensPedido() {
    const tokenElement = document.getElementById('token');
    if (!tokenElement) return;
    const token = tokenElement.value;

    if (!window.pedidoAtual || !window.pedidoAtual.numerodocumento) {
        return;
    }

    const url = `/novo-pedido/listar-itens?token=${token}&empresa=${window.pedidoAtual.empresa}&numerodocumento=${window.pedidoAtual.numerodocumento}`;

    fetch(url)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const tbody = document.getElementById('listaItens');
                if (!tbody) return;

                tbody.innerHTML = '';

                data.itens.forEach(item => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${item.codigoproduto}</td>
                        <td class="fw-semibold">${item.descricaoproduto}</td>
                        <td class="text-end">${item.quantidade.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                        <td class="text-end">R$ ${item.valorUnitario.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                        <td class="text-end text-danger">R$ ${(item.valorDesconto - item.valoracrescimo).toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                        <td class="text-end fw-bold">R$ ${item.valorTotal.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                        <td class="text-center">
                            <button type="button" class="btn btn-sm btn-outline-danger border-0" onclick="removerItem('${item.codigoproduto}')">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });

                // Atualiza os Totalizadores visuais na tela
                const lblBruto = document.getElementById('lblBruto');
                const lblDesconto = document.getElementById('lblDesconto');
                const lblAcrescimo = document.getElementById('lblAcrescimo');
                const lblLiquido = document.getElementById('lblLiquido');

                if (lblBruto) lblBruto.innerText = `R$ ${data.totais.bruto.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
                if (lblDesconto) lblDesconto.innerText = `R$ ${data.totais.desconto.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
                if (lblAcrescimo) lblAcrescimo.innerText = `R$ ${data.totais.acrescimo.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
                if (lblLiquido) lblLiquido.innerText = `R$ ${data.totais.liquido.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
            }
        })
        .catch(err => console.error("Erro na requisição de listagem de itens:", err));
}

// 🔹 Função para limpar o pedido atual (ao faturar ou cancelar)
function limparPedidoAtual() {
    localStorage.removeItem('pedidoEmAndamento');
    window.pedidoAtual = {
        empresa: 1,
        numerodocumento: null,
        codigovendedor: "001",
        codigocliente: "00001",
        codigocondPagamento: "001"
    };
    const tbody = document.getElementById('listaItens');
    if (tbody) tbody.innerHTML = '';
}