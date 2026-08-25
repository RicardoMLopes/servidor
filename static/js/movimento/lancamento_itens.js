// console.log("⚡ [lancamento_itens.js] Execução inicial do arquivo de script");

window.removerItem = async function(codigoproduto, seq) {
    // Tratamento de segurança para não travar
    const seqFinal = (seq && seq !== 'undefined' && seq !== 'null') ? seq : 0;

    if (!codigoproduto) {
        console.warn("⚠️ Código do produto não informado para exclusão.");
        return;
    }

    // 1. Solicita confirmação
    const confirmou = await mostrarModal({
        titulo: "Confirmar Exclusão",
        mensagem: `Deseja realmente remover o produto ${codigoproduto} do pedido?`,
        botoes: [
            { texto: "Cancelar", valor: false, classe: "btn-secondary" },
            { texto: "Sim, Remover", valor: true, classe: "btn-danger" }
        ]
    });

    if (!confirmou) return;

    const tokenElement = document.getElementById('token');
    if (!tokenElement) return;
    const token = tokenElement.value;

    const empresa = window.pedidoAtual?.empresa || 1;
    const numerodocumento = window.pedidoAtual?.numerodocumento;

    if (!numerodocumento) {
        await mostrarModal({
            titulo: "Atenção",
            mensagem: "Número do documento não encontrado.",
            botoes: [{ texto: "OK", valor: true, classe: "btn-primary" }]
        });
        return;
    }

    try {
        // 2. Chama a API
        const response = await fetch(`/novo-pedido/remover-item?token=${token}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                empresa: empresa,
                numerodocumento: numerodocumento,
                codigoproduto: codigoproduto,
                seq: seqFinal
            })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            console.log(`✅ Item ${codigoproduto} (seq: ${seqFinal}) removido com sucesso.`);

            if (typeof carregarItensPedido === 'function') {
                carregarItensPedido();
            }
        } else {
            await mostrarModal({
                titulo: "Erro ao Remover",
                mensagem: data.detail || "Não foi possível remover o item do pedido.",
                botoes: [{ texto: "Entendido", valor: false, classe: "btn-danger" }]
            });
        }
    } catch (err) {
        console.error("Erro ao tentar remover item:", err);
        await mostrarModal({
            titulo: "Erro do Servidor",
            mensagem: "Ocorreu uma falha de comunicação com o servidor.",
            botoes: [{ texto: "OK", valor: false, classe: "btn-danger" }]
        });
    }
};

// 🔹 Inicializa o pedido global apenas se não existir
if (typeof window.pedidoAtual === 'undefined') {
    const inputEmpresa = document.getElementById('empresa');
    const inputVendedor = document.getElementById('codigovendedor');
    const inputCliente = document.getElementById('codigocliente');
    const inputCondPag = document.getElementById('codigocondPagamento');

    window.pedidoAtual = {
        empresa: inputEmpresa ? inputEmpresa.value : 1,
        numerodocumento: null,
        codigovendedor: (inputVendedor && inputVendedor.value) ? inputVendedor.value : "",
        codigocliente: inputCliente ? inputCliente.value : "",
        codigocondPagamento: (inputCondPag && inputCondPag.value) ? inputCondPag.value : ""
    };
} else {
    console.log("ℹ️ [lancamento_itens.js] window.pedidoAtual JÁ EXISTIA:", JSON.stringify(window.pedidoAtual));
}

// 🔹 1. Função auxiliar blindada para salvar o estado no localStorage
function salvarEstadoPedido() {
    const elNome = document.getElementById('infoClienteNome');
    const elDoc = document.getElementById('infoClienteDoc');

    const inputEmpresa = document.getElementById('empresa');
    const inputVendedor = document.getElementById('codigovendedor');
    const inputCliente = document.getElementById('codigocliente');
    const inputCondPag = document.getElementById('codigocondPagamento');

    if (inputEmpresa && inputEmpresa.value) window.pedidoAtual.empresa = inputEmpresa.value;
    if (inputVendedor && inputVendedor.value) window.pedidoAtual.codigovendedor = inputVendedor.value;
    if (inputCliente && inputCliente.value) window.pedidoAtual.codigocliente = inputCliente.value;

    if (inputCondPag && inputCondPag.value) {
        window.pedidoAtual.codigocondPagamento = inputCondPag.value;
        window.pedidoAtual.codigocondpagamento = inputCondPag.value;
    }

    if (elNome && elNome.innerText.trim() !== "") window.pedidoAtual.nomecliente = elNome.innerText;
    if (elDoc && elDoc.innerText.trim() !== "") window.pedidoAtual.doccliente = elDoc.innerText;

    localStorage.setItem('pedidoEmAndamento', JSON.stringify(window.pedidoAtual));
}

// 🔹 Função inteligente para sincronizar o cabeçalho no Servidor
function sincronizarCabecalhoServidor() {
    const tokenElement = document.getElementById('token');
    if (!tokenElement) return;
    const token = tokenElement.value;

    const inputCli = document.getElementById('codigocliente');
    const clienteAtual = inputCli ? inputCli.value.trim() : (window.pedidoAtual?.codigocliente || "");

    if (!clienteAtual) return;

    const payload = {
        empresa: window.pedidoAtual.empresa || 1,
        numerodocumento: window.pedidoAtual.numerodocumento || null,
        codigocliente: clienteAtual,
        codigovendedor: window.pedidoAtual.codigovendedor || "",
        codigocondPagamento: window.pedidoAtual.codigocondPagamento || ""
    };

    fetch(`/novo-pedido/salvar-cabecalho?token=${token}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            if (!window.pedidoAtual.numerodocumento && data.numerodocumento) {
                window.pedidoAtual.numerodocumento = data.numerodocumento;
                const displayNum = document.getElementById('displayNumDocumento');
                if (displayNum) displayNum.innerText = data.numerodocumento;
            }

            window.pedidoAtual.empresa = data.empresa;
            window.pedidoAtual.codigocliente = data.codigocliente;
            window.pedidoAtual.nomecliente = data.nomecliente;
            window.pedidoAtual.codigovendedor = data.codigovendedor;
            window.pedidoAtual.codigocondPagamento = data.codigocondPagamento;

            const elNome = document.getElementById('infoClienteNome');
            if (elNome && data.nomecliente) elNome.innerText = data.nomecliente;

            salvarEstadoPedido();
            console.log("✅ [lancamento_itens.js] Cabeçalho salvo com sucesso:", window.pedidoAtual);
        } else {
            console.error("❌ [lancamento_itens.js] Erro ao salvar cabeçalho:", data.detail);
        }
    })
    .catch(err => console.error("❌ [lancamento_itens.js] Erro crítico na requisição:", err));
}

// 🔹 Ao carregar a página
document.addEventListener('DOMContentLoaded', () => {
    const inputClienteEl = document.getElementById('codigocliente');
    if (inputClienteEl) {
        inputClienteEl.addEventListener('blur', () => {
            if (inputClienteEl.value.trim() !== "") {
                window.pedidoAtual.codigocliente = inputClienteEl.value.trim();
                sincronizarCabecalhoServidor();
            }
        });
    }

    const urlParams = new URLSearchParams(window.location.search);
    const numeroUrl = urlParams.get('numerodocumento');

    if (numeroUrl) {
        window.pedidoAtual.numerodocumento = numeroUrl;
    } else {
        const pedidoSalvoLocal = JSON.parse(localStorage.getItem('pedidoEmAndamento'));
        if (pedidoSalvoLocal && pedidoSalvoLocal.numerodocumento) {
            window.pedidoAtual = pedidoSalvoLocal;

            const inputVendedor = document.getElementById('codigovendedor');
            const inputCliente = document.getElementById('codigocliente');
            const inputCondPag = document.getElementById('codigocondPagamento');

            if (inputVendedor && window.pedidoAtual.codigovendedor) inputVendedor.value = window.pedidoAtual.codigovendedor;
            if (inputCliente && window.pedidoAtual.codigocliente) inputCliente.value = window.pedidoAtual.codigocliente;
            if (inputCondPag && window.pedidoAtual.codigocondPagamento) {
                inputCondPag.value = window.pedidoAtual.codigocondPagamento;
            }
        }
    }

    if (window.pedidoAtual.numerodocumento) {
        const displayNum = document.getElementById('displayNumDocumento');
        if (displayNum) displayNum.innerText = window.pedidoAtual.numerodocumento;

        if (typeof carregarItensPedido === 'function') {
            carregarItensPedido();
        }
    }
});

// 🔹 Preenchimento do Modal de Edição
const modalCondicoesEl = document.getElementById('modalEditarCondicoes');
if (modalCondicoesEl) {
    modalCondicoesEl.addEventListener('show.bs.modal', function () {
        const tokenElement = document.getElementById('token');
        if (!tokenElement) return;
        const token = tokenElement.value;

        fetch(`/novo-pedido/listar-opcoes-condicoes?token=${token}`)
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const vendedorAtual = String(window.pedidoAtual.codigovendedor || '').trim();
                    const condPagAtual = String(
                        window.pedidoAtual.codigocondPagamento ||
                        window.pedidoAtual.codigocondpagamento ||
                        ''
                    ).trim();

                    // Select Vendedores
                    const selectVendedor = document.getElementById('selectVendedorModal');
                    if (selectVendedor) {
                        selectVendedor.innerHTML = '<option value="" disabled>Selecione um vendedor</option>';
                        data.vendedores.forEach(v => {
                            const codV = String(v.codigo).trim();
                            const selected = (codV === vendedorAtual || Number(codV) === Number(vendedorAtual)) ? 'selected' : '';
                            selectVendedor.innerHTML += `<option value="${v.codigo}" ${selected}>${v.codigo} - ${v.nome}</option>`;
                        });
                    }

                    // Select Condições
                    const selectCondPag = document.getElementById('selectCondPagModal');
                    if (selectCondPag) {
                        selectCondPag.innerHTML = '<option value="" disabled>Selecione uma condição</option>';
                        data.condicoes.forEach(c => {
                            const codC = String(c.codigo).trim();
                            const selected = (codC === condPagAtual || Number(codC) === Number(condPagAtual)) ? 'selected' : '';
                            selectCondPag.innerHTML += `<option value="${c.codigo}" ${selected}>${c.codigo} - ${c.descricao}</option>`;
                        });
                    }
                }
            })
            .catch(err => console.error("Erro no Modal:", err));
    });
}

async function salvarCondicoesPedido() {
    const selectVendedor = document.getElementById('selectVendedorModal');
    const selectCondPag = document.getElementById('selectCondPagModal');

    if (!selectVendedor || !selectCondPag) return;

    const novoVendedor = selectVendedor.value;
    const novaCondPag = selectCondPag.value;

    if (!novoVendedor || !novaCondPag) {
        await mostrarModal({
            titulo: "Atenção",
            mensagem: "Por favor, selecione o vendedor e a condição de pagamento.",
            botoes: [{ texto: "OK", valor: true, classe: "btn-primary" }]
        });
        return;
    }

    let nomeVendedorTexto = '';
    let nomeCondTexto = '';

    if (selectVendedor.selectedIndex >= 0) {
        const optText = selectVendedor.options[selectVendedor.selectedIndex].text;
        nomeVendedorTexto = optText.includes(' - ') ? optText.split(' - ').slice(1).join(' - ') : optText;
    }

    if (selectCondPag.selectedIndex >= 0) {
        const optText = selectCondPag.options[selectCondPag.selectedIndex].text;
        nomeCondTexto = optText.includes(' - ') ? optText.split(' - ').slice(1).join(' - ') : optText;
    }

    window.pedidoAtual.codigovendedor = novoVendedor;
    window.pedidoAtual.nomevendedor = nomeVendedorTexto;
    window.pedidoAtual.codigocondPagamento = novaCondPag;
    window.pedidoAtual.codigocondpagamento = novaCondPag;
    window.pedidoAtual.nomecondPagamento = nomeCondTexto;

    const inputVendedor = document.getElementById('codigovendedor');
    const inputCondPag = document.getElementById('codigocondPagamento');

    if (inputVendedor) inputVendedor.value = novoVendedor;
    if (inputCondPag) inputCondPag.value = novaCondPag;

    atualizarTextosVisiveisCards(novoVendedor, nomeVendedorTexto, novaCondPag, nomeCondTexto);
    salvarEstadoPedido();

    const modalCondicoesEl = document.getElementById('modalEditarCondicoes');
    if (modalCondicoesEl) {
        const modalInstance = bootstrap.Modal.getInstance(modalCondicoesEl);
        if (modalInstance) modalInstance.hide();
    }

    if (typeof sincronizarCabecalhoServidor === 'function') {
        sincronizarCabecalhoServidor();
    }
}

async function adicionarItemNaTabela() {
    const inputCli = document.getElementById('codigocliente');
    const inputVendedor = document.getElementById('codigovendedor');
    const inputCondPag = document.getElementById('codigocondPagamento');

    if (inputVendedor && inputVendedor.value) window.pedidoAtual.codigovendedor = inputVendedor.value;
    if (inputCondPag && inputCondPag.value) {
        window.pedidoAtual.codigocondPagamento = inputCondPag.value;
        window.pedidoAtual.codigocondpagamento = inputCondPag.value;
    }

    const tokenElement = document.getElementById('token');
    if (!tokenElement) return;
    const token = tokenElement.value;

    const inputUnitarioEl = document.getElementById('inputUnitario');

    const codigo = document.getElementById('inputCodigo').value;
    const descricao = document.getElementById('inputDescricao').value;
    const quantidade = parseFloat(document.getElementById('inputQtd').value) || 0;
    const valorUnitario = parseFloat(inputUnitarioEl?.value) || 0;

    // 🔹 RESGATE DO PREÇO BASE DE TABELA (cadproduto)
    const valorUnitarioVenda = parseFloat(inputUnitarioEl?.dataset?.precoVendaOriginal) || valorUnitario;

    let clienteParaEnviar = "";
    if (inputCli && inputCli.value.trim() !== "") {
        clienteParaEnviar = inputCli.value.trim();
    } else if (window.pedidoAtual && window.pedidoAtual.codigocliente) {
        clienteParaEnviar = window.pedidoAtual.codigocliente.trim();
    } else {
        clienteParaEnviar = window.dadosIniciais?.codigoClientePadrao || "";
    }

    window.pedidoAtual.codigocliente = clienteParaEnviar;

    if (!clienteParaEnviar || !codigo || quantidade <= 0 || valorUnitario <= 0) {
        await mostrarModal({
            titulo: "Atenção",
            mensagem: "Preencha todos os campos do item e selecione um cliente antes de adicionar.",
            botoes: [{ texto: "OK", valor: true, classe: "btn-primary" }]
        });
        return;
    }

    const payload = {
        empresa: window.pedidoAtual.empresa,
        numerodocumento: window.pedidoAtual.numerodocumento,
        codigovendedor: window.pedidoAtual.codigovendedor,
        codigocliente: clienteParaEnviar,
        codigocondPagamento: window.pedidoAtual.codigocondPagamento,
        item: {
            codigoproduto: codigo,
            descricaoproduto: descricao,
            quantidade: quantidade,
            valorUnitario: valorUnitario,            // 👈 Preço final negociado
            valorunitariovenda: valorUnitarioVenda,  // 👈 Preço base da tabela de preços
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
    .then(async data => {
        if (data.success) {
            window.pedidoAtual.empresa = data.empresa;
            window.pedidoAtual.numerodocumento = data.numerodocumento;
            window.pedidoAtual.codigocliente = data.codigocliente;
            window.pedidoAtual.codigovendedor = data.codigovendedor;
            window.pedidoAtual.codigocondPagamento = data.codigocondPagamento;

            if (data.nomevendedor) window.pedidoAtual.nomevendedor = data.nomevendedor;
            if (data.nomecondPagamento) window.pedidoAtual.nomecondPagamento = data.nomecondPagamento;

            atualizarTextosVisiveisCards(
                data.codigovendedor,
                data.nomevendedor,
                data.codigocondPagamento,
                data.nomecondPagamento
            );

            salvarEstadoPedido();

            window.itemEmEdicaoDescontoAcrescimo = null;

            // 🔹 Limpa os campos e o dataset do valor original
            document.getElementById('inputCodigo').value = '';
            document.getElementById('inputDescricao').value = '';
            document.getElementById('inputQtd').value = '1';
            if (inputUnitarioEl) {
                inputUnitarioEl.value = '0.00';
                delete inputUnitarioEl.dataset.precoVendaOriginal;
            }
            document.getElementById('inputCodigo').focus();

            if (typeof carregarItensPedido === 'function') {
                carregarItensPedido();
            }
        } else {
            await mostrarModal({
                titulo: "Erro ao Gravar Item",
                mensagem: data.detail || "Erro desconhecido ao adicionar item.",
                botoes: [{ texto: "Entendido", valor: false, classe: "btn-danger" }]
            });
        }
    })
    .catch(err => console.error("Erro na requisição:", err));
}

function carregarItensPedido() {
    const tokenElement = document.getElementById('token');
    if (!tokenElement) return;
    const token = tokenElement.value;

    if (!window.pedidoAtual || !window.pedidoAtual.numerodocumento) return;

    const url = `/novo-pedido/listar-itens?token=${token}&empresa=${window.pedidoAtual.empresa}&numerodocumento=${window.pedidoAtual.numerodocumento}`;

    fetch(url)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                if (data.codigocliente) {
                    window.pedidoAtual.codigocliente = data.codigocliente;
                    window.pedidoAtual.nomecliente = data.nomecliente;
                    const inputCliente = document.getElementById('codigocliente');
                    if (inputCliente) inputCliente.value = data.codigocliente;
                    const elNomeCliente = document.getElementById('infoClienteNome');
                    if (elNomeCliente) elNomeCliente.innerText = data.nomecliente;
                }

                if (data.codigovendedor) {
                    window.pedidoAtual.codigovendedor = data.codigovendedor;
                    if (data.nomevendedor) window.pedidoAtual.nomevendedor = data.nomevendedor;
                    const inputVendedor = document.getElementById('codigovendedor');
                    if (inputVendedor) inputVendedor.value = data.codigovendedor;
                }

                if (data.codigocondPagamento) {
                    window.pedidoAtual.codigocondPagamento = data.codigocondPagamento;
                    if (data.nomecondPagamento) window.pedidoAtual.nomecondPagamento = data.nomecondPagamento;
                    const inputCondPag = document.getElementById('codigocondPagamento');
                    if (inputCondPag) inputCondPag.value = data.codigocondPagamento;
                }

                atualizarTextosVisiveisCards(
                    data.codigovendedor,
                    data.nomevendedor,
                    data.codigocondPagamento,
                    data.nomecondPagamento
                );

                salvarEstadoPedido();

                const tbody = document.getElementById('listaItens');
                if (!tbody) return;

                tbody.innerHTML = '';

                data.itens.forEach(item => {
                    const tr = document.createElement('tr');
                    // 🔹 CORREÇÃO: Passa 'codigoproduto' E 'seq'
                    tr.innerHTML = `
                        <td>${item.codigoproduto}</td>
                        <td class="fw-semibold">${item.descricaoproduto}</td>
                        <td class="text-end">${item.quantidade.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                        <td class="text-end">R$ ${item.valorUnitario.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                        <td class="text-end text-danger">R$ ${(item.valorDesconto - item.valoracrescimo).toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                        <td class="text-end fw-bold">R$ ${item.valorTotal.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</td>
                        <td class="text-center">
                            <button type="button" class="btn btn-sm btn-outline-danger border-0" onclick="removerItem('${item.codigoproduto}', '${item.seq}')">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });

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

function limparPedidoAtual() {
    localStorage.removeItem('pedidoEmAndamento');
    window.pedidoAtual = {
        empresa: 1,
        numerodocumento: null,
        codigovendedor: "",
        codigocliente: "",
        codigocondPagamento: ""
    };
    const tbody = document.getElementById('listaItens');
    if (tbody) tbody.innerHTML = '';
}

function atualizarTextosVisiveisCards(vendedorCodigo, vendedorNome, condCodigo, condNome) {
    const infoVendedorNome = document.getElementById('infoVendedorNome');
    if (infoVendedorNome) {
        const codV = vendedorCodigo || window.pedidoAtual?.codigovendedor || '';
        const nomeV = vendedorNome || window.pedidoAtual?.nomevendedor || '';

        if (codV && nomeV && nomeV !== 'Nome') {
            infoVendedorNome.innerText = `${codV} - ${nomeV}`;
        } else if (codV) {
            infoVendedorNome.innerText = codV;
        }
    }

    const infoCondPagNome = document.getElementById('infoCondPagNome');
    if (infoCondPagNome) {
        const codC = condCodigo || window.pedidoAtual?.codigocondPagamento || window.pedidoAtual?.codigocondpagamento || '';
        const nomeC = condNome || window.pedidoAtual?.nomecondPagamento || '';

        if (codC && nomeC && nomeC !== 'Descrição') {
            infoCondPagNome.innerText = `${codC} - ${nomeC}`;
        } else if (codC) {
            infoCondPagNome.innerText = codC;
        }
    }
}

// 🔹 Função para disparar o recálculo via API ao alterar a Condição
async function recalcularPorCondicaoPagamento(novaCondPag) {
    if (!novaCondPag) return;

    const tokenElement = document.getElementById('token');
    if (!tokenElement) return;
    const token = tokenElement.value;

    const empresa = window.pedidoAtual?.empresa || 1;
    const numerodocumento = window.pedidoAtual?.numerodocumento;

    // Se ainda não salvou o pedido no banco, só atualiza na memória
    if (!numerodocumento) {
        window.pedidoAtual.codigocondPagamento = novaCondPag;
        salvarEstadoPedido();
        return;
    }

    try {
        const response = await fetch(`/novo-pedido/recalcular-condicao-pagamento?token=${token}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                empresa: empresa,
                numerodocumento: numerodocumento,
                codigocondPagamento: novaCondPag
            })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            window.pedidoAtual.codigocondPagamento = novaCondPag;
            salvarEstadoPedido();

            // 🔄 Recarrega a tabela e os totais instantaneamente na tela
            if (typeof carregarItensPedido === 'function') {
                carregarItensPedido();
            }

            console.log(`✅ Condição ${novaCondPag} aplicada e itens recalculados com sucesso!`);
        } else {
            await mostrarModal({
                titulo: "Erro ao Recalcular",
                mensagem: data.detail || "Não foi possível aplicar a nova condição de pagamento.",
                botoes: [{ texto: "OK", valor: false, classe: "btn-danger" }]
            });
        }
    } catch (err) {
        console.error("Erro na requisição de recálculo:", err);
    }
}

// 🔹 Escuta a seleção no Modal / Select da tela
document.addEventListener('DOMContentLoaded', () => {
    // 1. Caso a alteração ocorra dentro do Modal
    const selectCondPagModal = document.getElementById('selectCondPagModal');
    if (selectCondPagModal) {
        selectCondPagModal.addEventListener('change', (e) => {
            const novaCondicao = e.target.value;
            recalcularPorCondicaoPagamento(novaCondicao);
        });
    }

    // 2. Caso exista o input/select direto na tela principal
    const inputCondPagMain = document.getElementById('codigocondPagamento');
    if (inputCondPagMain) {
        inputCondPagMain.addEventListener('change', (e) => {
            const novaCondicao = e.target.value;
            recalcularPorCondicaoPagamento(novaCondicao);
        });
    }
});