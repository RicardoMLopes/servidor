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

                if (!data.itens || data.itens.length === 0) {
                    console.log("ℹ️ A lista de itens retornou vazia do banco.");
                }

                // 🛠️ Função auxiliar local para garantir 2 casas decimais estritas
                const fmt = (valor) => {
                    const num = parseFloat(valor) || 0;
                    return num.toLocaleString('pt-BR', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    });
                };

                // 📌 Percorre e renderiza cada item na tabela
                data.itens.forEach(item => {
                    const desc = parseFloat(item.valorDesconto) || 0;
                    const acres = parseFloat(item.valoracrescimo) || 0;
                    const diff = acres - desc; // Negativo = Desconto | Positivo = Acréscimo

                    // 1. Define a cor idêntica aos totalizadores inferiores
                    let classeCor = 'text-secondary';
                    if (diff < 0) classeCor = 'text-danger';
                    if (diff > 0) classeCor = 'text-success';

                    // 2. Define o texto formatado com o sinal correto
                    let textoDescAcres = 'R$ 0,00';
                    if (diff !== 0) {
                        const valorAbsoluto = fmt(Math.abs(diff));
                        textoDescAcres = diff < 0 ? `- R$ ${valorAbsoluto}` : `+ R$ ${valorAbsoluto}`;
                    }

                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${item.codigoproduto}</td>
                        <td class="fw-semibold">${item.descricaoproduto}</td>
                        <td class="text-end">${fmt(item.quantidade)}</td>
                        <td class="text-end">R$ ${fmt(item.valorUnitario)}</td>
                        <td class="text-end fw-semibold ${classeCor}">${textoDescAcres}</td>
                        <td class="text-end fw-bold">R$ ${fmt(item.valorTotal)}</td>
                        <td class="text-center">
                            <button type="button" class="btn btn-sm btn-outline-danger border-0" onclick="removerItem('${item.codigoproduto}')">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });

                // 📌 Atualiza os Totalizadores no Rodapé (Garantindo 2 casas decimais)
                if (data.totais) {
                    const lblBruto = document.getElementById('lblBruto');
                    const lblDesconto = document.getElementById('lblDesconto');
                    const lblAcrescimo = document.getElementById('lblAcrescimo');
                    const lblLiquido = document.getElementById('lblLiquido');

                    if (lblBruto) lblBruto.innerText = `R$ ${fmt(data.totais.bruto)}`;
                    if (lblDesconto) lblDesconto.innerText = `R$ ${fmt(data.totais.desconto)}`;
                    if (lblAcrescimo) lblAcrescimo.innerText = `R$ ${fmt(data.totais.acrescimo)}`;
                    if (lblLiquido) lblLiquido.innerText = `R$ ${fmt(data.totais.liquido)}`;
                }
            } else {
                console.error("❌ A API retornou sucesso falso:", data);
            }
        })
        .catch(err => console.error("❌ Erro na requisição de listagem de itens:", err));
}