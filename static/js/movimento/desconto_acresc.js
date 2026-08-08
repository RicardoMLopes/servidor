// 🔹 Exibe o limite carregado assim que o modal é aberto
document.getElementById('modalDescontoAcrescimoItem')?.addEventListener('show.bs.modal', function () {
    // Pega o limite que foi salvo na seleção do produto (ou 100% por padrão)
    const limite = window.limiteDescontoItemAtual !== undefined ? window.limiteDescontoItemAtual : 100.0;

    const lblLimite = document.getElementById('lblLimiteMaximo');
    if (lblLimite) {
        lblLimite.innerText = limite.toFixed(2);
    }

    // Reseta o input e validação ao abrir
    document.getElementById('modalItemDesconto').value = "0.00";
    document.getElementById('modalItemAcrescimo').value = "0.00";
    document.getElementById('tipoDescontoAcrescimo').value = "valor";
    alternarTipoDesconto("valor");
    validarDescontoEmTempoReal();
});

// 🔹 Alterna os rótulos entre Valor (R$) e Percentual (%)
function alternarTipoDesconto(tipo) {
    const lblDesconto = document.getElementById('labelDescontoInput');
    const lblAcrescimo = document.getElementById('labelAcrescimoInput');

    if (tipo === 'percentual') {
        if (lblDesconto) lblDesconto.innerText = "Desconto (%)";
        if (lblAcrescimo) lblAcrescimo.innerText = "Acréscimo (%)";
    } else {
        if (lblDesconto) lblDesconto.innerText = "Desconto (R$)";
        if (lblAcrescimo) lblAcrescimo.innerText = "Acréscimo (R$)";
    }
    validarDescontoEmTempoReal();
}

// 🔹 Valida em tempo real (converte valor para % se necessário e bloqueia se passar do teto)
function validarDescontoEmTempoReal() {
    const tipo = document.getElementById('tipoDescontoAcrescimo').value;
    const inputDesc = parseFloat(document.getElementById('modalItemDesconto').value) || 0;
    const inputField = document.getElementById('modalItemDesconto');
    const btnAplicar = document.getElementById('btnAplicarDesconto');

    const quantidade = parseFloat(document.getElementById('inputQtd').value) || 0;
    const valorUnitario = parseFloat(document.getElementById('inputUnitario').value) || 0;
    const valorBrutoTotal = quantidade * valorUnitario;

    let percentualAtual = 0;
    let limiteMaximo = window.limiteDescontoItemAtual !== undefined ? window.limiteDescontoItemAtual : 100.0;

    // Converte para percentual para podermos comparar de forma unificada
    if (tipo === 'percentual') {
        percentualAtual = inputDesc;
    } else {
        percentualAtual = valorBrutoTotal > 0 ? (inputDesc / valorBrutoTotal) * 100 : 0;
    }

    // Compara o percentual atual com o limite permitido
    if (percentualAtual > limiteMaximo) {
        inputField.classList.add('is-invalid'); // Deixa o input vermelho
        if (btnAplicar) {
            btnAplicar.disabled = true; // Bloqueia o botão Aplicar
            btnAplicar.classList.add('opacity-50');
        }
    } else {
        inputField.classList.remove('is-invalid'); // Remove o vermelho
        if (btnAplicar) {
            btnAplicar.disabled = false; // Libera o botão Aplicar
            btnAplicar.classList.remove('opacity-50');
        }
    }
}

// 🔹 Função acionada ao clicar em "Aplicar"
function aplicarDescontoAcrescimoItem() {
    const tipo = document.getElementById('tipoDescontoAcrescimo').value;
    const inputDesc = parseFloat(document.getElementById('modalItemDesconto').value) || 0;
    const inputAcres = parseFloat(document.getElementById('modalItemAcrescimo').value) || 0;

    const quantidade = parseFloat(document.getElementById('inputQtd').value) || 0;
    const valorUnitario = parseFloat(document.getElementById('inputUnitario').value) || 0;
    const valorBrutoTotal = quantidade * valorUnitario;

    let vDescCalculado = 0;
    let vAcresCalculado = 0;

    if (tipo === 'percentual') {
        vDescCalculado = (valorBrutoTotal * inputDesc) / 100;
        vAcresCalculado = (valorBrutoTotal * inputAcres) / 100;
    } else {
        vDescCalculado = inputDesc;
        vAcresCalculado = inputAcres;
    }

    // Validação final de segurança
    if (vDescCalculado > valorBrutoTotal) {
        alert("O valor do desconto não pode ser maior que o valor total do item.");
        return;
    }

    // Guarda os valores calculados
    window.itemEmEdicaoDescontoAcrescimo = {
        valorDesconto: vDescCalculado,
        valoracrescimo: vAcresCalculado
    };

    console.log("Desconto/Acréscimo aplicados:", window.itemEmEdicaoDescontoAcrescimo);

    // Resolve o problema de foco e fecha o modal de forma segura
    const btnAplicar = document.getElementById('btnAplicarDesconto');
    if (btnAplicar) btnAplicar.blur();

    const modalEl = document.getElementById('modalDescontoAcrescimoItem');
    const modalInstance = bootstrap.Modal.getInstance(modalEl);
    if (modalInstance) {
        modalInstance.hide();
    }
}