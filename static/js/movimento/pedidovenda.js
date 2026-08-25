document.addEventListener("DOMContentLoaded", async function() {
    console.log("--------------------------------------------------");
    console.log("🚀 [pedidovenda.js] 1. Evento DOMContentLoaded iniciado");

    const urlParams = new URLSearchParams(window.location.search);
    const numeroDocumentoUrl = urlParams.get('numerodocumento');
    const tokenElement = document.getElementById('token');
    const token = tokenElement ? tokenElement.value : '';

    console.log("📌 [pedidovenda.js] 2. Estado inicial:", {
        numeroDocumentoUrl,
        windowPedidoAtual: window.pedidoAtual,
        inputCondPagDOM: document.getElementById('codigocondPagamento')?.value
    });

    // 1. Tenta recuperar o que já estava no localStorage
    let pedidoSalvoLocal = null;
    try {
        const itemStorage = localStorage.getItem('pedidoEmAndamento');
        if (itemStorage && itemStorage.startsWith('{')) {
            pedidoSalvoLocal = JSON.parse(itemStorage);
            console.log("📦 [pedidovenda.js] 3. Dados lidos do localStorage:", pedidoSalvoLocal);
        }
    } catch (e) {
        console.error("❌ [pedidovenda.js] Erro ao ler localStorage:", e);
    }

    // Define o número do pedido ativo (URL tem prioridade)
    const numeroDocAtivo = numeroDocumentoUrl || pedidoSalvoLocal?.numerodocumento;
    const empresaAtiva = pedidoSalvoLocal?.empresa || window.dadosIniciais?.empresa || 1;

    // 2. Se for modo de ALTERAÇÃO / RESTAURAÇÃO (existe número de documento)
    if (numeroDocAtivo) {
        console.log("✏️ [pedidovenda.js] 4. Modo EDIÇÃO/RESTAURAÇÃO detectado para o pedido:", numeroDocAtivo);

        // Objeto inicial temporário
        window.pedidoAtual = {
            empresa: empresaAtiva,
            numerodocumento: numeroDocAtivo,
            codigovendedor: pedidoSalvoLocal?.codigovendedor || "",
            nomevendedor: pedidoSalvoLocal?.nomevendedor || "",
            codigocliente: pedidoSalvoLocal?.codigocliente || "",
            nomecliente: pedidoSalvoLocal?.nomecliente || "",
            doccliente: pedidoSalvoLocal?.doccliente || "",
            codigocondPagamento: pedidoSalvoLocal?.codigocondPagamento || "",
            nomecondPagamento: pedidoSalvoLocal?.nomecondPagamento || ""
        };

        console.log("⏳ [pedidovenda.js] 5. Estado ANTES de buscar no Banco:", JSON.stringify(window.pedidoAtual));

        // 🟢 BUSCA OS DADOS REAIS DO CABEÇALHO DIRETO DO BANCO DE DADOS
        if (token) {
            try {
                console.log("📡 [pedidovenda.js] 6. Disparando Fetch /listar-itens...");
                const response = await fetch(`/novo-pedido/listar-itens?token=${token}&empresa=${empresaAtiva}&numerodocumento=${numeroDocAtivo}`);
                const data = await response.json();

                if (data.success) {
                    console.log("✅ [pedidovenda.js] 7. Resposta do Banco recebida:", data);

                    if (data.codigovendedor) window.pedidoAtual.codigovendedor = data.codigovendedor;
                    if (data.nomevendedor) window.pedidoAtual.nomevendedor = data.nomevendedor;
                    if (data.codigocondPagamento) window.pedidoAtual.codigocondPagamento = data.codigocondPagamento;
                    if (data.nomecondPagamento) window.pedidoAtual.nomecondPagamento = data.nomecondPagamento;
                    if (data.codigocliente) window.pedidoAtual.codigocliente = data.codigocliente;
                    if (data.nomecliente) window.pedidoAtual.nomecliente = data.nomecliente;

                    console.log("🎯 [pedidovenda.js] 8. window.pedidoAtual APÓS atualização do Banco:", JSON.stringify(window.pedidoAtual));
                }
            } catch (err) {
                console.error("⚠️ [pedidovenda.js] Não foi possível sincronizar com o banco:", err);
            }
        }

        // 3. Atualiza os elementos HTML do DOM com a VERDADE do banco de dados
        const displayNum = document.getElementById('displayNumDocumento');
        if (displayNum) displayNum.innerText = window.pedidoAtual.numerodocumento;

        const elNome = document.getElementById('infoClienteNome');
        const elDoc = document.getElementById('infoClienteDoc');
        if (elNome && window.pedidoAtual.nomecliente) elNome.innerText = window.pedidoAtual.nomecliente;
        if (elDoc && window.pedidoAtual.doccliente) elDoc.innerText = window.pedidoAtual.doccliente;

        const inputEmpresa = document.getElementById('empresa');
        const inputVendedor = document.getElementById('codigovendedor');
        const inputCliente = document.getElementById('codigocliente');
        const inputCondPag = document.getElementById('codigocondPagamento');

        if (inputEmpresa) inputEmpresa.value = window.pedidoAtual.empresa;
        if (inputVendedor) inputVendedor.value = window.pedidoAtual.codigovendedor;
        if (inputCliente) inputCliente.value = window.pedidoAtual.codigocliente;
        if (inputCondPag) {
            console.log(`📝 [pedidovenda.js] 9. Escrevendo valor "${window.pedidoAtual.codigocondPagamento}" no input #codigocondPagamento`);
            inputCondPag.value = window.pedidoAtual.codigocondPagamento;
        }

        // 4. Atualiza os Cards Visíveis
        if (typeof atualizarTextosVisiveisCards === 'function') {
            console.log("🎨 [pedidovenda.js] 10. Chamando atualizarTextosVisiveisCards()");
            atualizarTextosVisiveisCards(
                window.pedidoAtual.codigovendedor,
                window.pedidoAtual.nomevendedor,
                window.pedidoAtual.codigocondPagamento,
                window.pedidoAtual.nomecondPagamento
            );
        }

        // 5. Salva o estado atualizado no localStorage
        localStorage.setItem('pedidoEmAndamento', JSON.stringify(window.pedidoAtual));

        // 6. Carrega a tabela de itens
        if (typeof carregarItensPedido === 'function') {
            console.log("📋 [pedidovenda.js] 11. Chamando carregarItensPedido()");
            carregarItensPedido();
        }

    } else {
        console.log("🆕 [pedidovenda.js] Modo NOVO PEDIDO LIMPO...");
        const inputEmpresa = document.getElementById('empresa');
        const inputVendedor = document.getElementById('codigovendedor');
        const inputCliente = document.getElementById('codigocliente');
        const inputCondPag = document.getElementById('codigocondPagamento');

        let clienteInicial = (inputCliente && inputCliente.value.trim() !== "")
            ? inputCliente.value.trim()
            : (window.dadosIniciais?.codigoClientePadrao || "");

        if (inputCliente) inputCliente.value = clienteInicial;

        window.pedidoAtual = {
            empresa: inputEmpresa ? inputEmpresa.value : 1,
            numerodocumento: null,
            codigovendedor: inputVendedor ? inputVendedor.value : "",
            nomevendedor: "",
            codigocliente: clienteInicial,
            nomecliente: "",
            codigocondPagamento: inputCondPag ? inputCondPag.value : "",
            nomecondPagamento: ""
        };

        if (typeof salvarEstadoPedido === 'function') {
            salvarEstadoPedido();
        }
    }
    console.log("--------------------------------------------------");
});