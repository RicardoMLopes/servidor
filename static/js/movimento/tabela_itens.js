function carregarItensPedido() {
    const tokenElement = document.getElementById('token');
    if (!tokenElement) {
        console.error("❌ Elemento 'token' não foi encontrado no HTML!");
        return;
    }
    const token = tokenElement.value;

    if (!window.pedidoAtual || !window.pedidoAtual.numerodocumento) {
        console.warn("⚠️ Nenhum número de documento definido em window.pedidoAtual.");
        return;
    }

    const url = `/novo-pedido/listar-itens?token=${token}&empresa=${window.pedidoAtual.empresa}&numerodocumento=${window.pedidoAtual.numerodocumento}`;
    console.log("🔍 Buscando itens na URL:", url);

    fetch(url)
        .then(res => res.json())
        .then(data => {
            console.log("📦 Dados recebidos da API de listagem:", data);

            if (data.success) {
                const tbody = document.getElementById('listaItens');
                if (!tbody) {
                    console.error("❌ Elemento 'listaItens' (tbody) não foi encontrado no HTML!");
                    return;
                }

                tbody.innerHTML = '';

                if (data.itens.length === 0) {
                    console.log("ℹ️ A lista de itens retornou vazia do banco.");
                }

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

                // Atualiza os Totalizadores na Tela
                document.getElementById('lblBruto').innerText = `R$ ${data.totais.bruto.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
                document.getElementById('lblDesconto').innerText = `R$ ${data.totais.desconto.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
                document.getElementById('lblAcrescimo').innerText = `R$ ${data.totais.acrescimo.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
                document.getElementById('lblLiquido').innerText = `R$ ${data.totais.liquido.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
            } else {
                console.error("❌ A API retornou sucesso falso:", data);
            }
        })
        .catch(err => console.error("❌ Erro na requisição de listagem de itens:", err));
}