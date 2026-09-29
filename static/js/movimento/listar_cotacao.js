document.getElementById("filtroCotacoes")?.addEventListener("input", function () {
    const termo = this.value.toLowerCase();

    document.querySelectorAll("#tabelaCotacoes tbody tr").forEach(function (linha) {
        linha.style.display = linha.innerText.toLowerCase().includes(termo)
            ? ""
            : "none";
    });
});

async function faturarTodos(numerodocumento) {
    const confirmar = await Swal.fire({
        title: "Faturar cotação?",
        text: "Todos os itens desta cotação serão transformados em pedido.",
        icon: "question",
        showCancelButton: true,
        confirmButtonText: "Sim, faturar todos",
        cancelButtonText: "Cancelar"
    });

    if (!confirmar.isConfirmed) {
        return;
    }

    try {
        const resposta = await fetch(
            `/cotacao/faturar-todos?numerodocumento=${numerodocumento}`,
            {
                method: "POST"
            }
        );

        const dados = await resposta.json();

        if (!resposta.ok) {
            throw new Error(
                dados.detail || "Erro ao faturar cotação."
            );
        }

        await Swal.fire({
            icon: "success",
            title: "Cotação faturada",
            text: dados.mensagem ||
                "Todos os itens foram transformados em pedido.",
            confirmButtonText: "OK"
        });

        window.location.reload();

    } catch (erro) {
        Swal.fire({
            icon: "error",
            title: "Erro",
            text: erro.message
        });
    }
}

async function faturarItem(numerodocumento, seq, quantidadeSaldo) {
    const resultado = await Swal.fire({
        title: "Faturar item",
        text: "Informe a quantidade que deseja transformar em pedido.",
        input: "number",
        inputValue: quantidadeSaldo,
        inputAttributes: {
            min: 0.01,
            max: quantidadeSaldo,
            step: 0.01
        },
        showCancelButton: true,
        confirmButtonText: "Faturar",
        cancelButtonText: "Cancelar",
        inputValidator: (valor) => {
            const quantidade = parseFloat(valor);

            if (!valor || isNaN(quantidade)) {
                return "Informe uma quantidade.";
            }

            if (quantidade <= 0) {
                return "A quantidade deve ser maior que zero.";
            }

            if (quantidade > quantidadeSaldo) {
                return `A quantidade máxima disponível é ${quantidadeSaldo}.`;
            }

            return undefined;
        }
    });

    if (!resultado.isConfirmed) {
        return;
    }

    const quantidade = parseFloat(resultado.value);

    try {
        const resposta = await fetch(
            `/cotacao/faturar-item?numerodocumento=${numerodocumento}` +
            `&seq=${seq}&quantidade=${quantidade}`,
            {
                method: "POST"
            }
        );

        const dados = await resposta.json();

        if (!resposta.ok) {
            throw new Error(
                dados.detail || "Erro ao faturar item."
            );
        }

        await Swal.fire({
            icon: "success",
            title: "Item faturado",
            text: dados.mensagem ||
                "Quantidade faturada com sucesso.",
            confirmButtonText: "OK"
        });

        window.location.reload();

    } catch (erro) {
        Swal.fire({
            icon: "error",
            title: "Erro",
            text: erro.message
        });
    }
}