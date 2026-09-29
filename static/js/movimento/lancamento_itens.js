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
            botoes: [
                { texto: "OK", valor: true, classe: "btn-primary" }
            ]
        });
        return;
    }

    try {
        const response = await fetch(
            `/novo-pedido/remover-item?token=${token}`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    empresa: empresa,
                    numerodocumento: numerodocumento,
                    codigoproduto: codigoproduto,
                    seq: seqFinal
                })
            }
        );

        const data = await response.json();

        if (response.ok && data.success) {
            console.log(
                `✅ Item ${codigoproduto} (seq: ${seqFinal}) removido com sucesso.`
            );

            if (typeof carregarItensPedido === 'function') {
                carregarItensPedido();
            }
        } else {
            await mostrarModal({
                titulo: "Erro ao Remover",
                mensagem: data.detail || "Não foi possível remover o item do pedido.",
                botoes: [
                    {
                        texto: "Entendido",
                        valor: false,
                        classe: "btn-danger"
                    }
                ]
            });
        }
    } catch (err) {
        console.error("Erro ao tentar remover item:", err);

        await mostrarModal({
            titulo: "Erro do Servidor",
            mensagem: "Ocorreu uma falha de comunicação com o servidor.",
            botoes: [
                {
                    texto: "OK",
                    valor: false,
                    classe: "btn-danger"
                }
            ]
        });
    }
};

// Inicializa o pedido global apenas se ainda não existir.
// A definição de NOVO ou EDITAR fica por conta do pedidovenda.js.
if (typeof window.pedidoAtual === 'undefined') {
    const inputEmpresa = document.getElementById('empresa');
    const inputVendedor = document.getElementById('codigovendedor');
    const inputCliente = document.getElementById('codigocliente');
    const inputCondPag = document.getElementById('codigocondPagamento');

    window.pedidoAtual = {
        empresa: inputEmpresa ? inputEmpresa.value : 1,
        numerodocumento: null,
        codigovendedor: (
            inputVendedor && inputVendedor.value
        ) ? inputVendedor.value : "",
        codigocliente: inputCliente ? inputCliente.value : "",
        codigocondPagamento: (
            inputCondPag && inputCondPag.value
        ) ? inputCondPag.value : ""
    };
} else {
    console.log(
        "ℹ️ [lancamento_itens.js] window.pedidoAtual JÁ EXISTIA:",
        JSON.stringify(window.pedidoAtual)
    );
}

// Salva o estado atual dos campos do cabeçalho no objeto em memória.
// Não utiliza localStorage para controlar o documento.
function salvarEstadoPedido() {
    const elNome = document.getElementById('infoClienteNome');
    const elDoc = document.getElementById('infoClienteDoc');

    const inputEmpresa = document.getElementById('empresa');
    const inputVendedor = document.getElementById('codigovendedor');
    const inputCliente = document.getElementById('codigocliente');
    const inputCondPag = document.getElementById('codigocondPagamento');

    if (inputEmpresa && inputEmpresa.value) {
        window.pedidoAtual.empresa = inputEmpresa.value;
    }

    if (inputVendedor && inputVendedor.value) {
        window.pedidoAtual.codigovendedor = inputVendedor.value;
    }

    if (inputCliente && inputCliente.value) {
        window.pedidoAtual.codigocliente = inputCliente.value;
    }

    if (inputCondPag && inputCondPag.value) {
        window.pedidoAtual.codigocondPagamento = inputCondPag.value;
        window.pedidoAtual.codigocondpagamento = inputCondPag.value;
    }

    if (elNome && elNome.innerText.trim() !== "") {
        window.pedidoAtual.nomecliente = elNome.innerText;
    }

    if (elDoc && elDoc.innerText.trim() !== "") {
        window.pedidoAtual.doccliente = elDoc.innerText;
    }
}

// Sincroniza o cabeçalho com o servidor.
function sincronizarCabecalhoServidor() {
    const tokenElement = document.getElementById('token');
    if (!tokenElement) return;

    const token = tokenElement.value;

    const inputCli = document.getElementById('codigocliente');

    const clienteAtual = inputCli
        ? inputCli.value.trim()
        : (window.pedidoAtual?.codigocliente || "");

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
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                if (
                    !window.pedidoAtual.numerodocumento &&
                    data.numerodocumento
                ) {
                    window.pedidoAtual.numerodocumento =
                        data.numerodocumento;

                    const displayNum =
                        document.getElementById('displayNumDocumento');

                    if (displayNum) {
                        displayNum.innerText = data.numerodocumento;
                    }
                }

                window.pedidoAtual.empresa = data.empresa;
                window.pedidoAtual.codigocliente = data.codigocliente;
                window.pedidoAtual.nomecliente = data.nomecliente;
                window.pedidoAtual.codigovendedor = data.codigovendedor;
                window.pedidoAtual.codigocondPagamento =
                    data.codigocondPagamento;

                const elNome =
                    document.getElementById('infoClienteNome');

                if (elNome && data.nomecliente) {
                    elNome.innerText = data.nomecliente;
                }

                salvarEstadoPedido();

                console.log(
                    "✅ [lancamento_itens.js] Cabeçalho salvo com sucesso:",
                    window.pedidoAtual
                );
            } else {
                console.error(
                    "❌ [lancamento_itens.js] Erro ao salvar cabeçalho:",
                    data.detail
                );
            }
        })
        .catch(err => {
            console.error(
                "❌ [lancamento_itens.js] Erro crítico na requisição:",
                err
            );
        });
}

// Ao carregar a página.
// IMPORTANTE:
// - Não lê localStorage.
// - Não decide NOVO/EDITAR.
// - Não chama carregarItensPedido().
// O pedidovenda.js controla essa parte.
document.addEventListener('DOMContentLoaded', () => {
    const inputClienteEl =
        document.getElementById('codigocliente');

    if (inputClienteEl) {
        inputClienteEl.addEventListener('blur', () => {
            if (inputClienteEl.value.trim() !== "") {
                window.pedidoAtual.codigocliente =
                    inputClienteEl.value.trim();

                sincronizarCabecalhoServidor();
            }
        });
    }
});

// Preenchimento do Modal de Edição
const modalCondicoesEl =
    document.getElementById('modalEditarCondicoes');

if (modalCondicoesEl) {
    modalCondicoesEl.addEventListener(
        'show.bs.modal',
        function() {
            const tokenElement =
                document.getElementById('token');

            if (!tokenElement) return;

            const token = tokenElement.value;

            fetch(
                `/novo-pedido/listar-opcoes-condicoes?token=${token}`
            )
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        const vendedorAtual =
                            String(
                                window.pedidoAtual.codigovendedor || ''
                            ).trim();

                        const condPagAtual =
                            String(
                                window.pedidoAtual.codigocondPagamento ||
                                window.pedidoAtual.codigocondpagamento ||
                                ''
                            ).trim();

                        // Select Vendedores
                        const selectVendedor =
                            document.getElementById(
                                'selectVendedorModal'
                            );

                        if (selectVendedor) {
                            selectVendedor.innerHTML =
                                '<option value="" disabled>' +
                                'Selecione um vendedor' +
                                '</option>';

                            data.vendedores.forEach(v => {
                                const codV =
                                    String(v.codigo).trim();

                                const selected =
                                    (
                                        codV === vendedorAtual ||
                                        Number(codV) ===
                                        Number(vendedorAtual)
                                    )
                                        ? 'selected'
                                        : '';

                                selectVendedor.innerHTML +=
                                    `<option value="${v.codigo}" ${selected}>` +
                                    `${v.codigo} - ${v.nome}` +
                                    `</option>`;
                            });
                        }

                        // Select Condições
                        const selectCondPag =
                            document.getElementById(
                                'selectCondPagModal'
                            );

                        if (selectCondPag) {
                            selectCondPag.innerHTML =
                                '<option value="" disabled>' +
                                'Selecione uma condição' +
                                '</option>';

                            data.condicoes.forEach(c => {
                                const codC =
                                    String(c.codigo).trim();

                                const selected =
                                    (
                                        codC === condPagAtual ||
                                        Number(codC) ===
                                        Number(condPagAtual)
                                    )
                                        ? 'selected'
                                        : '';

                                selectCondPag.innerHTML +=
                                    `<option value="${c.codigo}" ${selected}>` +
                                    `${c.codigo} - ${c.descricao}` +
                                    `</option>`;
                            });
                        }
                    }
                })
                .catch(err =>
                    console.error("Erro no Modal:", err)
                );
        }
    );
}

async function salvarCondicoesPedido() {
    const selectVendedor =
        document.getElementById('selectVendedorModal');

    const selectCondPag =
        document.getElementById('selectCondPagModal');

    if (!selectVendedor || !selectCondPag) return;

    const novoVendedor = selectVendedor.value;
    const novaCondPag = selectCondPag.value;

    if (!novoVendedor || !novaCondPag) {
        await mostrarModal({
            titulo: "Atenção",
            mensagem:
                "Por favor, selecione o vendedor e a condição de pagamento.",
            botoes: [
                {
                    texto: "OK",
                    valor: true,
                    classe: "btn-primary"
                }
            ]
        });
        return;
    }

    let nomeVendedorTexto = '';
    let nomeCondTexto = '';

    if (selectVendedor.selectedIndex >= 0) {
        const optText =
            selectVendedor.options[
                selectVendedor.selectedIndex
            ].text;

        nomeVendedorTexto =
            optText.includes(' - ')
                ? optText.split(' - ').slice(1).join(' - ')
                : optText;
    }

    if (selectCondPag.selectedIndex >= 0) {
        const optText =
            selectCondPag.options[
                selectCondPag.selectedIndex
            ].text;

        nomeCondTexto =
            optText.includes(' - ')
                ? optText.split(' - ').slice(1).join(' - ')
                : optText;
    }

    window.pedidoAtual.codigovendedor = novoVendedor;
    window.pedidoAtual.nomevendedor = nomeVendedorTexto;

    window.pedidoAtual.codigocondPagamento = novaCondPag;
    window.pedidoAtual.codigocondpagamento = novaCondPag;
    window.pedidoAtual.nomecondPagamento = nomeCondTexto;

    const inputVendedor =
        document.getElementById('codigovendedor');

    const inputCondPag =
        document.getElementById('codigocondPagamento');

    if (inputVendedor) {
        inputVendedor.value = novoVendedor;
    }

    if (inputCondPag) {
        inputCondPag.value = novaCondPag;
    }

    atualizarTextosVisiveisCards(
        novoVendedor,
        nomeVendedorTexto,
        novaCondPag,
        nomeCondTexto
    );

    salvarEstadoPedido();

    const modalCondicoesEl =
        document.getElementById('modalEditarCondicoes');

    if (modalCondicoesEl) {
        const modalInstance =
            bootstrap.Modal.getInstance(modalCondicoesEl);

        if (modalInstance) {
            modalInstance.hide();
        }
    }

    if (
        typeof sincronizarCabecalhoServidor === 'function'
    ) {
        sincronizarCabecalhoServidor();
    }
}

async function adicionarItemNaTabela() {
    const inputCli =
        document.getElementById('codigocliente');

    const inputVendedor =
        document.getElementById('codigovendedor');

    const inputCondPag =
        document.getElementById('codigocondPagamento');

    if (inputVendedor && inputVendedor.value) {
        window.pedidoAtual.codigovendedor =
            inputVendedor.value;
    }

    if (inputCondPag && inputCondPag.value) {
        window.pedidoAtual.codigocondPagamento =
            inputCondPag.value;

        window.pedidoAtual.codigocondpagamento =
            inputCondPag.value;
    }

    const tokenElement =
        document.getElementById('token');

    if (!tokenElement) return;

    const token = tokenElement.value;

    const inputUnitarioEl =
        document.getElementById('inputUnitario');

    const codigo =
        document.getElementById('inputCodigo').value;

    const descricao =
        document.getElementById('inputDescricao').value;

    const quantidade =
        parseFloat(
            document.getElementById('inputQtd').value
        ) || 0;

    const valorUnitario =
        parseFloat(inputUnitarioEl?.value) || 0;

    const valorUnitarioVenda =
        parseFloat(
            inputUnitarioEl?.dataset?.precoVendaOriginal
        ) || valorUnitario;

    let clienteParaEnviar = "";

    if (inputCli && inputCli.value.trim() !== "") {
        clienteParaEnviar = inputCli.value.trim();
    } else if (
        window.pedidoAtual &&
        window.pedidoAtual.codigocliente
    ) {
        clienteParaEnviar =
            window.pedidoAtual.codigocliente.trim();
    } else {
        clienteParaEnviar =
            window.dadosIniciais?.codigoClientePadrao || "";
    }

    window.pedidoAtual.codigocliente =
        clienteParaEnviar;

    if (
        !clienteParaEnviar ||
        !codigo ||
        quantidade <= 0 ||
        valorUnitario <= 0
    ) {
        await mostrarModal({
            titulo: "Atenção",
            mensagem:
                "Preencha todos os campos do item e selecione um cliente antes de adicionar.",
            botoes: [
                {
                    texto: "OK",
                    valor: true,
                    classe: "btn-primary"
                }
            ]
        });
        return;
    }

    const payload = {
        empresa: window.pedidoAtual.empresa,
        numerodocumento:
            window.pedidoAtual.numerodocumento,
        codigovendedor:
            window.pedidoAtual.codigovendedor,
        codigocliente: clienteParaEnviar,
        codigocondPagamento:
            window.pedidoAtual.codigocondPagamento,
        item: {
            codigoproduto: codigo,
            descricaoproduto: descricao,
            quantidade: quantidade,
            valorUnitario: valorUnitario,
            valorunitariovenda: valorUnitarioVenda,
            valorDesconto:
                window.itemEmEdicaoDescontoAcrescimo?.valorDesconto || 0,
            valoracrescimo:
                window.itemEmEdicaoDescontoAcrescimo?.valoracrescimo || 0
        }
    };

    fetch(
        `/novo-pedido/adicionar-item?token=${token}`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        }
    )
        .then(res => res.json())
        .then(async data => {
            if (data.success) {
                window.pedidoAtual.empresa =
                    data.empresa;

                window.pedidoAtual.numerodocumento =
                    data.numerodocumento;

                window.pedidoAtual.codigocliente =
                    data.codigocliente;

                window.pedidoAtual.codigovendedor =
                    data.codigovendedor;

                window.pedidoAtual.codigocondPagamento =
                    data.codigocondPagamento;

                if (data.nomevendedor) {
                    window.pedidoAtual.nomevendedor =
                        data.nomevendedor;
                }

                if (data.nomecondPagamento) {
                    window.pedidoAtual.nomecondPagamento =
                        data.nomecondPagamento;
                }

                atualizarTextosVisiveisCards(
                    data.codigovendedor,
                    data.nomevendedor,
                    data.codigocondPagamento,
                    data.nomecondPagamento
                );

                salvarEstadoPedido();

                window.itemEmEdicaoDescontoAcrescimo =
                    null;

                document.getElementById(
                    'inputCodigo'
                ).value = '';

                document.getElementById(
                    'inputDescricao'
                ).value = '';

                document.getElementById(
                    'inputQtd'
                ).value = '1';

                if (inputUnitarioEl) {
                    inputUnitarioEl.value = '0.00';

                    delete inputUnitarioEl.dataset
                        .precoVendaOriginal;
                }

                document.getElementById(
                    'inputCodigo'
                ).focus();

                if (
                    typeof carregarItensPedido ===
                    'function'
                ) {
                    carregarItensPedido();
                }
            } else {
                await mostrarModal({
                    titulo: "Erro ao Gravar Item",
                    mensagem:
                        data.detail ||
                        "Erro desconhecido ao adicionar item.",
                    botoes: [
                        {
                            texto: "Entendido",
                            valor: false,
                            classe: "btn-danger"
                        }
                    ]
                });
            }
        })
        .catch(err =>
            console.error(
                "Erro na requisição:",
                err
            )
        );
}

function limparPedidoAtual() {
    window.pedidoAtual = {
        empresa: 1,
        numerodocumento: null,
        codigovendedor: "",
        codigocliente: "",
        codigocondPagamento: ""
    };

    const tbody =
        document.getElementById('listaItens');

    if (tbody) {
        tbody.innerHTML = '';
    }
}

function atualizarTextosVisiveisCards(
    vendedorCodigo,
    vendedorNome,
    condCodigo,
    condNome
) {
    const infoVendedorNome =
        document.getElementById('infoVendedorNome');

    if (infoVendedorNome) {
        const codV =
            vendedorCodigo ||
            window.pedidoAtual?.codigovendedor ||
            '';

        const nomeV =
            vendedorNome ||
            window.pedidoAtual?.nomevendedor ||
            '';

        if (codV && nomeV && nomeV !== 'Nome') {
            infoVendedorNome.innerText =
                `${codV} - ${nomeV}`;
        } else if (codV) {
            infoVendedorNome.innerText = codV;
        }
    }

    const infoCondPagNome =
        document.getElementById('infoCondPagNome');

    if (infoCondPagNome) {
        const codC =
            condCodigo ||
            window.pedidoAtual?.codigocondPagamento ||
            window.pedidoAtual?.codigocondpagamento ||
            '';

        const nomeC =
            condNome ||
            window.pedidoAtual?.nomecondPagamento ||
            '';

        if (codC && nomeC && nomeC !== 'Descrição') {
            infoCondPagNome.innerText =
                `${codC} - ${nomeC}`;
        } else if (codC) {
            infoCondPagNome.innerText = codC;
        }
    }
}

// Função para disparar o recálculo via API ao alterar a Condição
async function recalcularPorCondicaoPagamento(novaCondPag) {
    if (!novaCondPag) return;

    const tokenElement =
        document.getElementById('token');

    if (!tokenElement) return;

    const token = tokenElement.value;

    const empresa =
        window.pedidoAtual?.empresa || 1;

    const numerodocumento =
        window.pedidoAtual?.numerodocumento;

    // Se ainda não salvou o pedido no banco,
    // só atualiza na memória.
    if (!numerodocumento) {
        window.pedidoAtual.codigocondPagamento =
            novaCondPag;

        salvarEstadoPedido();
        return;
    }

    try {
        const response = await fetch(
            `/novo-pedido/recalcular-condicao-pagamento?token=${token}`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    empresa: empresa,
                    numerodocumento: numerodocumento,
                    codigocondPagamento: novaCondPag
                })
            }
        );

        const data = await response.json();

        if (response.ok && data.success) {
            window.pedidoAtual.codigocondPagamento =
                novaCondPag;

            salvarEstadoPedido();

            if (
                typeof carregarItensPedido ===
                'function'
            ) {
                carregarItensPedido();
            }

            console.log(
                `✅ Condição ${novaCondPag} aplicada e itens recalculados com sucesso!`
            );
        } else {
            await mostrarModal({
                titulo: "Erro ao Recalcular",
                mensagem:
                    data.detail ||
                    "Não foi possível aplicar a nova condição de pagamento.",
                botoes: [
                    {
                        texto: "OK",
                        valor: false,
                        classe: "btn-danger"
                    }
                ]
            });
        }
    } catch (err) {
        console.error(
            "Erro na requisição de recálculo:",
            err
        );
    }
}

// Escuta a seleção no Modal / Select da tela
document.addEventListener('DOMContentLoaded', () => {
    const selectCondPagModal =
        document.getElementById(
            'selectCondPagModal'
        );

    if (selectCondPagModal) {
        selectCondPagModal.addEventListener(
            'change',
            e => {
                const novaCondicao =
                    e.target.value;

                recalcularPorCondicaoPagamento(
                    novaCondicao
                );
            }
        );
    }

    const inputCondPagMain =
        document.getElementById(
            'codigocondPagamento'
        );

    if (inputCondPagMain) {
        inputCondPagMain.addEventListener(
            'change',
            e => {
                const novaCondicao =
                    e.target.value;

                recalcularPorCondicaoPagamento(
                    novaCondicao
                );
            }
        );
    }
});