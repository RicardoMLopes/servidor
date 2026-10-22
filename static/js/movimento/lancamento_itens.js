console.log("🚀 [lancamento_itens.js] Arquivo carregado com sucesso!");

// ============================================================
// 1. DADOS E MODAL DE INFORMAÇÕES ADICIONAIS DO ITEM
// ============================================================
let dadosInformativosItemAtual = {
    data_pedido_previsto: null,
    ordem_compra: null,
    item_ordem_compra: null,
    material: null,
    referencia: null
};

/**
 * Abre o modal de Informações Adicionais preenchendo com os valores atuais
 */
window.abrirModalInfAdicionais = function() {
    console.log("📂 [lancamento_itens.js] Abrindo modal de Inf. Adicionais...");

    const elData = document.getElementById("modalDataPrevista");
    const elOC = document.getElementById("modalOrdemCompra");
    const elItemOC = document.getElementById("modalItemOrdem");
    const elMat = document.getElementById("modalMaterial");
    const elRef = document.getElementById("modalReferencia");

    if (elData) elData.value = dadosInformativosItemAtual.data_pedido_previsto || "";
    if (elOC) elOC.value = dadosInformativosItemAtual.ordem_compra || "";
    if (elItemOC) elItemOC.value = dadosInformativosItemAtual.item_ordem_compra || "";
    if (elMat) elMat.value = dadosInformativosItemAtual.material || "";
    if (elRef) elRef.value = dadosInformativosItemAtual.referencia || "";

    const modalEl = document.getElementById("modalItemDetalhes");
    if (modalEl) {
        const modalInstance = new bootstrap.Modal(modalEl);
        modalInstance.show();
    } else {
        console.warn("⚠️ Elemento #modalItemDetalhes não encontrado no DOM.");
    }
};


// ============================================================
// 2. EXCLUSÃO DE ITENS
// ============================================================
window.removerItem = async function(codigoproduto, seq) {
    const seqFinal = (seq && seq !== 'undefined' && seq !== 'null') ? seq : 0;

    if (!codigoproduto) {
        console.warn("⚠️ Código do produto não informado para exclusão.");
        return;
    }

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


// ============================================================
// 3. GERENCIAMENTO DO ESTADO DO PEDIDO E CABEÇALHO
// ============================================================
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
}

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
}

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


// ============================================================
// 4. ADICIONAR ITEM NA TABELA (ENVIANDO DADOS + INF. ADICIONAIS)
// ============================================================
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
    const urlParams = new URLSearchParams(window.location.search);
    const token = tokenElement ? tokenElement.value : (urlParams.get("token") || localStorage.getItem("token") || "");

    if (!token) {
        alert("Token de autenticação não encontrado!");
        return;
    }

    const inputUnitarioEl = document.getElementById('inputUnitario');
    const codigo = document.getElementById('inputCodigo')?.value.trim() || '';
    const descricao = document.getElementById('inputDescricao')?.value.trim() || '';
    const quantidade = parseFloat(document.getElementById('inputQtd')?.value || 0);
    const valorUnitario = parseFloat(inputUnitarioEl?.value) || 0;
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
        empresa: parseInt(window.pedidoAtual.empresa || 1),
        numerodocumento: parseInt(window.pedidoAtual.numerodocumento || 0) || null,
        codigovendedor: window.pedidoAtual.codigovendedor || "",
        codigocliente: clienteParaEnviar,
        codigocondPagamento: window.pedidoAtual.codigocondPagamento || "",
        tipodocumento: urlParams.get("tipodocumento") || "COTACAO",
        item: {
            codigoproduto: codigo,
            descricaoproduto: descricao,
            quantidade: quantidade,
            quantidade_pedida: quantidade,
            valorUnitario: valorUnitario,
            valorunitariovenda: valorUnitarioVenda,
            valorDesconto: window.itemEmEdicaoDescontoAcrescimo?.valorDesconto || 0,
            valoracrescimo: window.itemEmEdicaoDescontoAcrescimo?.valoracrescimo || 0,
            data_pedido_previsto: dadosInformativosItemAtual.data_pedido_previsto,
            ordem_compra: dadosInformativosItemAtual.ordem_compra,
            item_ordem_compra: dadosInformativosItemAtual.item_ordem_compra,
            material: dadosInformativosItemAtual.material,
            referencia: dadosInformativosItemAtual.referencia
        }
    };

    console.log("📦 [lancamento_itens.js] Enviando item para o backend:", payload);

    try {
        const response = await fetch(`/novo-pedido/adicionar-item?token=${encodeURIComponent(token)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            await mostrarModal({
                titulo: "Erro ao Gravar Item",
                mensagem: data.detail || "Erro desconhecido ao adicionar item.",
                botoes: [{ texto: "Entendido", valor: false, classe: "btn-danger" }]
            });
            return;
        }

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

        dadosInformativosItemAtual = {
            data_pedido_previsto: null,
            ordem_compra: null,
            item_ordem_compra: null,
            material: null,
            referencia: null
        };
        const badge = document.getElementById("badgeInfAdicionais");
        if (badge) badge.style.display = "none";

        const inputCod = document.getElementById('inputCodigo');
        const inputDesc = document.getElementById('inputDescricao');
        const inputQtd = document.getElementById('inputQtd');

        if (inputCod) inputCod.value = '';
        if (inputDesc) inputDesc.value = '';
        if (inputQtd) inputQtd.value = '1';

        if (inputUnitarioEl) {
            inputUnitarioEl.value = '0.00';
            delete inputUnitarioEl.dataset.precoVendaOriginal;
        }

        if (inputCod) inputCod.focus();

        if (typeof carregarItensPedido === 'function') {
            carregarItensPedido();
        } else if (typeof carregarItensDoPedido === 'function') {
            carregarItensDoPedido();
        }

    } catch (err) {
        console.error("❌ Erro crítico na requisição:", err);
        alert("Erro ao conectar com o servidor.");
    }
}


// ============================================================
// 5. EVENT LISTENERS E INICIALIZAÇÃO
// ============================================================
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

    const btnSalvarModal = document.getElementById("btnSalvarModalItem");
    if (btnSalvarModal) {
        btnSalvarModal.addEventListener("click", function () {
            if (document.activeElement) {
                document.activeElement.blur();
            }

            const dataPrevista = document.getElementById("modalDataPrevista")?.value || "";
            const ordemCompra = document.getElementById("modalOrdemCompra")?.value.trim() || "";
            const itemOrdem = document.getElementById("modalItemOrdem")?.value.trim() || "";
            const material = document.getElementById("modalMaterial")?.value.trim() || "";
            const referencia = document.getElementById("modalReferencia")?.value.trim() || "";

            dadosInformativosItemAtual = {
                data_pedido_previsto: dataPrevista || null,
                ordem_compra: ordemCompra || null,
                item_ordem_compra: itemOrdem || null,
                material: material || null,
                referencia: referencia || null
            };

            const badge = document.getElementById("badgeInfAdicionais");
            if (badge) {
                const temDados = Object.values(dadosInformativosItemAtual).some(v => v !== null && v !== "");
                badge.style.display = temDados ? "inline-block" : "none";
            }

            const modalEl = document.getElementById("modalItemDetalhes");
            if (modalEl) {
                const modalInstance = bootstrap.Modal.getInstance(modalEl);
                if (modalInstance) modalInstance.hide();
            }
        });
    }

    const selectCondPagModal = document.getElementById('selectCondPagModal');
    if (selectCondPagModal) {
        selectCondPagModal.addEventListener('change', e => {
            recalcularPorCondicaoPagamento(e.target.value);
        });
    }

    const inputCondPagMain = document.getElementById('codigocondPagamento');
    if (inputCondPagMain) {
        inputCondPagMain.addEventListener('change', e => {
            recalcularPorCondicaoPagamento(e.target.value);
        });
    }
});


// ============================================================
// 6. FUNÇÕES AUXILIARES DE SUPORTE
// ============================================================
function limparPedidoAtual() {
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

async function recalcularPorCondicaoPagamento(novaCondPag) {
    if (!novaCondPag) return;

    const tokenElement = document.getElementById('token');
    if (!tokenElement) return;

    const token = tokenElement.value;
    const empresa = window.pedidoAtual?.empresa || 1;
    const numerodocumento = window.pedidoAtual?.numerodocumento;

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