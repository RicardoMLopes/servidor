function carregarItensPedido() {
    const urlParams = new URLSearchParams(window.location.search);
    const numeroDocumentoUrl = urlParams.get('numerodocumento');

    // Só busca itens quando o documento foi informado explicitamente na URL.
    // Documento novo não deve consultar itens antigos.
    if (!numeroDocumentoUrl) {
        console.log("🆕 [tabela_itens.js] Novo documento. Nenhum item será carregado do banco.");
        return;
    }

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

    // Garante que o documento consultado é o mesmo informado na URL.
    const numeroDocumento = numeroDocumentoUrl;

    const url =
        `/novo-pedido/listar-itens?token=${token}` +
        `&empresa=${window.pedidoAtual.empresa}` +
        `&numerodocumento=${numeroDocumento}`;

    console.log("🔍 [tabela_itens.js] Buscando itens na URL:", url);

    fetch(url)
        .then(res => res.json())
        .then(data => {
            console.log("📦 [tabela_itens.js] Dados recebidos da API:", data);

            if (!data.success) {
                console.error("❌ A API retornou sucesso falso:", data);
                return;
            }

            const tbody = document.getElementById('listaItens');

            if (!tbody) {
                console.error("❌ Elemento 'listaItens' não foi encontrado no HTML!");
                return;
            }

            tbody.innerHTML = '';

            if (!data.itens || data.itens.length === 0) {
                console.log("ℹ️ A lista de itens retornou vazia do banco.");
            }

            const fmt = (valor) => {
                const num = parseFloat(valor) || 0;

                return num.toLocaleString('pt-BR', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
            };

            data.itens.forEach(item => {
                const desc = parseFloat(item.valorDesconto) || 0;
                const acres = parseFloat(item.valoracrescimo) || 0;
                const diff = acres - desc;

                let classeCor = 'text-secondary';

                if (diff < 0) {
                    classeCor = 'text-danger';
                }

                if (diff > 0) {
                    classeCor = 'text-success';
                }

                let textoDescAcres = 'R$ 0,00';

                if (diff !== 0) {
                    const valorAbsoluto = fmt(Math.abs(diff));

                    textoDescAcres = diff < 0
                        ? `- R$ ${valorAbsoluto}`
                        : `+ R$ ${valorAbsoluto}`;
                }

                const tr = document.createElement('tr');

                tr.innerHTML = `
                    <td>${item.codigoproduto}</td>
                    <td class="fw-semibold">${item.descricaoproduto}</td>
                    <td class="text-end">${fmt(item.quantidade)}</td>
                    <td class="text-end">R$ ${fmt(item.valorUnitario)}</td>
                    <td class="text-end fw-semibold ${classeCor}">
                        ${textoDescAcres}
                    </td>
                    <td class="text-end fw-bold">
                        R$ ${fmt(item.valorTotal)}
                    </td>
                    <td class="text-center">
                        <button
                            type="button"
                            class="btn btn-sm btn-outline-danger border-0"
                            onclick="removerItem('${item.codigoproduto}')">
                            <i class="bi bi-trash"></i>
                        </button>
                    </td>
                `;

                tbody.appendChild(tr);
            });

            if (data.totais) {
                const lblBruto = document.getElementById('lblBruto');
                const lblDesconto = document.getElementById('lblDesconto');
                const lblAcrescimo = document.getElementById('lblAcrescimo');
                const lblLiquido = document.getElementById('lblLiquido');

                if (lblBruto) {
                    lblBruto.innerText = `R$ ${fmt(data.totais.bruto)}`;
                }

                if (lblDesconto) {
                    lblDesconto.innerText = `R$ ${fmt(data.totais.desconto)}`;
                }

                if (lblAcrescimo) {
                    lblAcrescimo.innerText = `R$ ${fmt(data.totais.acrescimo)}`;
                }

                if (lblLiquido) {
                    lblLiquido.innerText = `R$ ${fmt(data.totais.liquido)}`;
                }
            }
        })
        .catch(err => {
            console.error(
                "❌ [tabela_itens.js] Erro na requisição de listagem:",
                err
            );
        });
}