console.log("⚡ [lancamento_itens.js] Execução inicial do arquivo de script");

// 🔹 Inicializa o pedido global apenas se não existir
if (typeof window.pedidoAtual === 'undefined') {
    const inputEmpresa = document.getElementById('empresa');
    const inputVendedor = document.getElementById('codigovendedor');
    const inputCliente = document.getElementById('codigocliente');
    const inputCondPag = document.getElementById('codigocondPagamento');

    console.log("⚠️ [lancamento_itens.js] window.pedidoAtual era UNDEFINED. Criando objeto inicial com dados do DOM:", {
        vendedorDOM: inputVendedor?.value,
        condPagDOM: inputCondPag?.value
    });

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
    console.log("💾 [lancamento_itens.js] Executando salvarEstadoPedido()...");
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
        console.log(`⚠️ [lancamento_itens.js] salvarEstadoPedido lendo do input #codigocondPagamento: "${inputCondPag.value}"`);
        window.pedidoAtual.codigocondPagamento = inputCondPag.value;
        window.pedidoAtual.codigocondpagamento = inputCondPag.value;
    }

    if (elNome && elNome.innerText.trim() !== "") window.pedidoAtual.nomecliente = elNome.innerText;
    if (elDoc && elDoc.innerText.trim() !== "") window.pedidoAtual.doccliente = elDoc.innerText;

    localStorage.setItem('pedidoEmAndamento', JSON.stringify(window.pedidoAtual));
    console.log("💾 [lancamento_itens.js] Estado salvo:", JSON.stringify(window.pedidoAtual));
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

    console.log("🔄 [lancamento_itens.js] Sincronizando cabeçalho com o servidor:", payload);

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
    console.log("--------------------------------------------------");
    console.log("🚀 [lancamento_itens.js] Evento DOMContentLoaded iniciado");

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
        console.log("📌 [lancamento_itens.js] Número na URL detectado:", numeroUrl);
        window.pedidoAtual.numerodocumento = numeroUrl;
    } else {
        const pedidoSalvoLocal = JSON.parse(localStorage.getItem('pedidoEmAndamento'));
        if (pedidoSalvoLocal && pedidoSalvoLocal.numerodocumento) {
            console.log("📦 [lancamento_itens.js] Lendo localStorage no DOMContentLoaded:", pedidoSalvoLocal);
            window.pedidoAtual = pedidoSalvoLocal;

            const inputVendedor = document.getElementById('codigovendedor');
            const inputCliente = document.getElementById('codigocliente');
            const inputCondPag = document.getElementById('codigocondPagamento');

            if (inputVendedor && window.pedidoAtual.codigovendedor) inputVendedor.value = window.pedidoAtual.codigovendedor;
            if (inputCliente && window.pedidoAtual.codigocliente) inputCliente.value = window.pedidoAtual.codigocliente;
            if (inputCondPag && window.pedidoAtual.codigocondPagamento) {
                console.log(`📝 [lancamento_itens.js] Forçando valor "${window.pedidoAtual.codigocondPagamento}" do localStorage no Input HTML`);
                inputCondPag.value = window.pedidoAtual.codigocondPagamento;
            }
        }
    }

    if (window.pedidoAtual.numerodocumento) {
        console.log("🔎 [lancamento_itens.js] Executando carregarItensPedido() via DOMContentLoaded");
        const displayNum = document.getElementById('displayNumDocumento');
        if (displayNum) displayNum.innerText = window.pedidoAtual.numerodocumento;

        if (typeof carregarItensPedido === 'function') {
            carregarItensPedido();
        }
    }
    console.log("--------------------------------------------------");
});

// 🔹 Preenchimento do Modal de Edição
const modalCondicoesEl = document.getElementById('modalEditarCondicoes');
if (modalCondicoesEl) {
    modalCondicoesEl.addEventListener('show.bs.modal', function () {
        console.log("👁️ [lancamento_itens.js] Modal de Condições aberto!");
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

                    console.log("⚙️ [lancamento_itens.js] Selecionando no Modal:", { vendedorAtual, condPagAtual });

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

function salvarCondicoesPedido() {
    const selectVendedor = document.getElementById('selectVendedorModal');
    const selectCondPag = document.getElementById('selectCondPagModal');

    if (!selectVendedor || !selectCondPag) return;

    const novoVendedor = selectVendedor.value;
    const novaCondPag = selectCondPag.value;

    if (!novoVendedor || !novaCondPag) {
        alert("Por favor, selecione o vendedor e a condição de pagamento.");
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

    console.log("💾 [lancamento_itens.js] Salvando Condições do Modal:", { novoVendedor, novaCondPag });

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

function adicionarItemNaTabela() {
    console.log("➕ [lancamento_itens.js] Adicionar item clicado!");
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

    const codigo = document.getElementById('inputCodigo').value;
    const descricao = document.getElementById('inputDescricao').value;
    const quantidade = parseFloat(document.getElementById('inputQtd').value) || 0;
    const valorUnitario = parseFloat(document.getElementById('inputUnitario').value) || 0;

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
        alert("Preencha todos os campos do item e selecione um cliente.");
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
            valorUnitario: valorUnitario,
            valorDesconto: window.itemEmEdicaoDescontoAcrescimo?.valorDesconto || 0,
            valoracrescimo: window.itemEmEdicaoDescontoAcrescimo?.valoracrescimo || 0
        }
    };

    console.log("📡 [lancamento_itens.js] Enviando item:", payload);

    fetch(`/novo-pedido/adicionar-item?token=${token}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            console.log("✅ [lancamento_itens.js] Item adicionado com sucesso, resposta banco:", data);
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

            document.getElementById('inputCodigo').value = '';
            document.getElementById('inputDescricao').value = '';
            document.getElementById('inputQtd').value = '1';
            document.getElementById('inputUnitario').value = '0.00';
            document.getElementById('inputCodigo').focus();

            if (typeof carregarItensPedido === 'function') {
                carregarItensPedido();
            }
        } else {
            alert("Erro ao gravar item: " + (data.detail || "Erro desconhecido"));
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
    console.log("📡 [lancamento_itens.js] Executando carregarItensPedido(). URL:", url);

    fetch(url)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                console.log("📊 [lancamento_itens.js] Resposta do carregarItensPedido():", data);
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
    console.log("🧹 [lancamento_itens.js] Limpando dados do pedido...");
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
    console.log("🎨 [lancamento_itens.js] Atualizando cards da UI com:", { vendedorCodigo, vendedorNome, condCodigo, condNome });
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