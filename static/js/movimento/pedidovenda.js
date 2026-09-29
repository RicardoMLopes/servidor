document.addEventListener("DOMContentLoaded", async function() {
    console.log("--------------------------------------------------");
    console.log("🚀 [pedidovenda.js] 1. Evento DOMContentLoaded iniciado");

    const urlParams = new URLSearchParams(window.location.search);
    const numeroDocumentoUrl = urlParams.get('numerodocumento');

    const tokenElement = document.getElementById('token');
    const token = tokenElement ? tokenElement.value : '';

    const empresaAtiva =
        window.dadosIniciais?.empresa ||
        document.getElementById('empresa')?.value ||
        1;

    console.log("📌 [pedidovenda.js] 2. Estado inicial:", {
        numeroDocumentoUrl,
        dadosIniciais: window.dadosIniciais,
        windowPedidoAtual: window.pedidoAtual,
        inputCondPagDOM:
            document.getElementById('codigocondPagamento')?.value
    });

    // ============================================================
    // MODO EDIÇÃO
    // A existência de numerodocumento na URL é a única indicação
    // de que estamos editando um documento existente.
    // ============================================================
    if (numeroDocumentoUrl) {
        console.log(
            "✏️ [pedidovenda.js] 3. Modo EDIÇÃO detectado:",
            numeroDocumentoUrl
        );

        window.pedidoAtual = {
            empresa: empresaAtiva,
            numerodocumento: numeroDocumentoUrl,
            codigovendedor: "",
            nomevendedor: "",
            codigocliente: "",
            nomecliente: "",
            doccliente: "",
            codigocondPagamento: "",
            nomecondPagamento: ""
        };

        console.log(
            "⏳ [pedidovenda.js] 4. Estado ANTES de buscar no Banco:",
            JSON.stringify(window.pedidoAtual)
        );

        // Busca os dados reais do documento no banco.
        if (token) {
            try {
                console.log(
                    "📡 [pedidovenda.js] 5. Disparando Fetch /listar-itens..."
                );

                const response = await fetch(
                    `/novo-pedido/listar-itens?token=${token}` +
                    `&empresa=${empresaAtiva}` +
                    `&numerodocumento=${numeroDocumentoUrl}`
                );

                const data = await response.json();

                if (data.success) {
                    console.log(
                        "✅ [pedidovenda.js] 6. Resposta do Banco recebida:",
                        data
                    );

                    if (data.codigovendedor) {
                        window.pedidoAtual.codigovendedor =
                            data.codigovendedor;
                    }

                    if (data.nomevendedor) {
                        window.pedidoAtual.nomevendedor =
                            data.nomevendedor;
                    }

                    if (data.codigocondPagamento) {
                        window.pedidoAtual.codigocondPagamento =
                            data.codigocondPagamento;
                    }

                    if (data.nomecondPagamento) {
                        window.pedidoAtual.nomecondPagamento =
                            data.nomecondPagamento;
                    }

                    if (data.codigocliente) {
                        window.pedidoAtual.codigocliente =
                            data.codigocliente;
                    }

                    if (data.nomecliente) {
                        window.pedidoAtual.nomecliente =
                            data.nomecliente;
                    }

                    if (data.doccliente) {
                        window.pedidoAtual.doccliente =
                            data.doccliente;
                    }

                    console.log(
                        "🎯 [pedidovenda.js] 7. window.pedidoAtual APÓS atualização do Banco:",
                        JSON.stringify(window.pedidoAtual)
                    );
                } else {
                    console.error(
                        "❌ [pedidovenda.js] API retornou sucesso falso:",
                        data
                    );
                }
            } catch (err) {
                console.error(
                    "⚠️ [pedidovenda.js] Não foi possível sincronizar com o banco:",
                    err
                );
            }
        } else {
            console.warn(
                "⚠️ [pedidovenda.js] Token não encontrado."
            );
        }

        // ========================================================
        // Atualiza os elementos HTML com os dados do documento
        // ========================================================

        const displayNum =
            document.getElementById('displayNumDocumento');

        if (displayNum) {
            displayNum.innerText =
                window.pedidoAtual.numerodocumento;
        }

        const elNome =
            document.getElementById('infoClienteNome');

        const elDoc =
            document.getElementById('infoClienteDoc');

        if (elNome && window.pedidoAtual.nomecliente) {
            elNome.innerText =
                window.pedidoAtual.nomecliente;
        }

        if (elDoc && window.pedidoAtual.doccliente) {
            elDoc.innerText =
                window.pedidoAtual.doccliente;
        }

        const inputEmpresa =
            document.getElementById('empresa');

        const inputVendedor =
            document.getElementById('codigovendedor');

        const inputCliente =
            document.getElementById('codigocliente');

        const inputCondPag =
            document.getElementById('codigocondPagamento');

        if (inputEmpresa) {
            inputEmpresa.value =
                window.pedidoAtual.empresa;
        }

        if (inputVendedor) {
            inputVendedor.value =
                window.pedidoAtual.codigovendedor;
        }

        if (inputCliente) {
            inputCliente.value =
                window.pedidoAtual.codigocliente;
        }

        if (inputCondPag) {
            console.log(
                `📝 [pedidovenda.js] 8. Escrevendo condição "${window.pedidoAtual.codigocondPagamento}"`
            );

            inputCondPag.value =
                window.pedidoAtual.codigocondPagamento;
        }

        // Atualiza os cards visíveis.
        if (
            typeof atualizarTextosVisiveisCards ===
            'function'
        ) {
            console.log(
                "🎨 [pedidovenda.js] 9. Atualizando Cards"
            );

            atualizarTextosVisiveisCards(
                window.pedidoAtual.codigovendedor,
                window.pedidoAtual.nomevendedor,
                window.pedidoAtual.codigocondPagamento,
                window.pedidoAtual.nomecondPagamento
            );
        }

        // ========================================================
        // SOMENTE EDIÇÃO:
        // carrega os itens do documento informado na URL.
        // ========================================================
        if (
            typeof carregarItensPedido ===
            'function'
        ) {
            console.log(
                "📋 [pedidovenda.js] 10. Carregando itens do documento existente"
            );

            carregarItensPedido();
        }

    } else {
        // ============================================================
        // MODO NOVO
        // Não usa localStorage.
        // Não busca documento anterior.
        // Não carrega itens do banco.
        // ============================================================

        console.log(
            "🆕 [pedidovenda.js] 3. Modo NOVO DOCUMENTO"
        );

        const inputEmpresa =
            document.getElementById('empresa');

        const inputVendedor =
            document.getElementById('codigovendedor');

        const inputCliente =
            document.getElementById('codigocliente');

        const inputCondPag =
            document.getElementById('codigocondPagamento');

        // Número novo fornecido pelo backend.
        const numeroNovo =
            window.dadosIniciais?.numerodocumento ||
            null;

        // Cliente padrão.
        const clienteInicial =
            inputCliente &&
            inputCliente.value.trim() !== ""
                ? inputCliente.value.trim()
                : (
                    window.dadosIniciais
                        ?.codigoClientePadrao || ""
                );

        if (inputCliente) {
            inputCliente.value =
                clienteInicial;
        }

        // Cria o estado limpo do novo documento.
        window.pedidoAtual = {
            empresa:
                inputEmpresa
                    ? inputEmpresa.value
                    : empresaAtiva,

            numerodocumento:
                numeroNovo,

            codigovendedor:
                inputVendedor
                    ? inputVendedor.value
                    : (
                        window.dadosIniciais
                            ?.codigoVendedor || ""
                    ),

            nomevendedor: "",

            codigocliente:
                clienteInicial,

            nomecliente:
                window.dadosIniciais
                    ?.nomeClientePadrao || "",

            doccliente:
                window.dadosIniciais
                    ?.docClientePadrao || "",

            codigocondPagamento:
                inputCondPag
                    ? inputCondPag.value
                    : "",

            nomecondPagamento: ""
        };

        console.log(
            "🆕 [pedidovenda.js] Novo documento definido:",
            JSON.stringify(window.pedidoAtual)
        );

        // Mostra o novo número na tela.
        const displayNum =
            document.getElementById(
                'displayNumDocumento'
            );

        if (displayNum && numeroNovo) {
            displayNum.innerText =
                numeroNovo;
        }

        // Atualiza o cliente padrão.
        const elNome =
            document.getElementById(
                'infoClienteNome'
            );

        const elDoc =
            document.getElementById(
                'infoClienteDoc'
            );

        if (
            elNome &&
            window.pedidoAtual.nomecliente
        ) {
            elNome.innerText =
                window.pedidoAtual.nomecliente;
        }

        if (
            elDoc &&
            window.pedidoAtual.doccliente
        ) {
            elDoc.innerText =
                window.pedidoAtual.doccliente;
        }

        // Atualiza os cards.
        if (
            typeof atualizarTextosVisiveisCards ===
            'function'
        ) {
            atualizarTextosVisiveisCards(
                window.pedidoAtual.codigovendedor,
                window.pedidoAtual.nomevendedor,
                window.pedidoAtual.codigocondPagamento,
                window.pedidoAtual.nomecondPagamento
            );
        }

        // IMPORTANTE:
        // Não chama carregarItensPedido() aqui.
        // Documento novo começa sem itens carregados do banco.
    }

    console.log("--------------------------------------------------");
});