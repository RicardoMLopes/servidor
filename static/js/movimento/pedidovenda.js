// Tenta carregar do localStorage (Caso tenha sido um F5)
const pedidoSalvoLocal = JSON.parse(localStorage.getItem('pedidoEmAndamento'));

window.pedidoAtual = pedidoSalvoLocal || {
    empresa: window.dadosIniciais?.empresa || 1,
    numerodocumento: null,
    codigovendedor: window.dadosIniciais?.codigoVendedor || "001",
    codigocliente: window.dadosIniciais?.codigoClientePadrao || "",
    codigocondPagamento: window.dadosIniciais?.codigoCondPagamentoPadrao || "001"
};

document.addEventListener("DOMContentLoaded", function() {
    const pedidoSalvoLocal = JSON.parse(localStorage.getItem('pedidoEmAndamento'));

    // Se existe um pedido em andamento salvo no navegador E ele tem número de documento
    if (pedidoSalvoLocal && pedidoSalvoLocal.numerodocumento) {
        window.pedidoAtual = pedidoSalvoLocal;
        console.log("Restaurando pedido ativo após F5/Ctrl+R:", window.pedidoAtual.numerodocumento);

        // 1. Restaura o Número do Documento no Topo
        const displayNum = document.getElementById('displayNumDocumento');
        if (displayNum) displayNum.innerText = window.pedidoAtual.numerodocumento;

        // 2. Restaura visualmente o Card do Cliente
        const elNome = document.getElementById('infoClienteNome');
        const elDoc = document.getElementById('infoClienteDoc');
        if (elNome && window.pedidoAtual.nomecliente) elNome.innerText = window.pedidoAtual.nomecliente;
        if (elDoc && window.pedidoAtual.doccliente) elDoc.innerText = window.pedidoAtual.doccliente;

        // 3. Atualiza os Inputs Ocultos com os valores salvos
        const inputEmpresa = document.getElementById('empresa');
        const inputVendedor = document.getElementById('codigovendedor');
        const inputCliente = document.getElementById('codigocliente');
        const inputCondPag = document.getElementById('codigocondPagamento');

        if (inputEmpresa) inputEmpresa.value = window.pedidoAtual.empresa;
        if (inputVendedor) inputVendedor.value = window.pedidoAtual.codigovendedor;
        if (inputCliente) inputCliente.value = window.pedidoAtual.codigocliente;
        if (inputCondPag) inputCondPag.value = window.pedidoAtual.codigocondPagamento;

        // 4. Carrega os itens na tabela
        if (typeof carregarItensPedido === 'function') {
            carregarItensPedido();
        }
    } else {
        // Se for um novo pedido limpo, inicializa com os dados correntes dos inputs do FastAPI
        const inputEmpresa = document.getElementById('empresa');
        const inputVendedor = document.getElementById('codigovendedor');
        const inputCliente = document.getElementById('codigocliente');
        const inputCondPag = document.getElementById('codigocondPagamento');

        window.pedidoAtual = {
            empresa: inputEmpresa ? inputEmpresa.value : 1,
            numerodocumento: null,
            codigovendedor: inputVendedor ? inputVendedor.value : "001",
            codigocliente: inputCliente ? inputCliente.value : "",
            codigocondPagamento: inputCondPag ? inputCondPag.value : "001"
        };

        salvarEstadoPedido();
    }
});