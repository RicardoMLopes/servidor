document.addEventListener("DOMContentLoaded", () => {

    const formEmpresa = document.getElementById("formEmpresa");
    const loader = document.getElementById("loader");
    const msgErro = document.getElementById("msgErro");
    const empresaDados = document.getElementById("empresaDados");
    const nomeEmpresa = document.getElementById("nomeEmpresa");
    const cnpjEmpresa = document.getElementById("cnpjEmpresa");
    const cnpjInput = document.getElementById("cnpj");

    function mostrar(elemento) {
        elemento.classList.remove("d-none");
    }

    function ocultar(elemento) {
        elemento.classList.add("d-none");
    }

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) {
            return parts.pop().split(";").shift();
        }
    }

    // Verifica se a empresa já foi identificada
    const empresaCnpj = getCookie("empresa_cnpj");
    const empresaToken = getCookie("empresa_token");

    if (empresaCnpj && empresaToken) {
        mostrar(empresaDados);
        nomeEmpresa.textContent = "Empresa já reconhecida";
        cnpjEmpresa.textContent = empresaCnpj;

        setTimeout(() => {
            window.location.href = "/dashboard/";
        }, 1000);

        return;
    }

    formEmpresa.addEventListener("submit", async (e) => {

        e.preventDefault();

        const cnpj = cnpjInput.value.trim().replace(/\D/g, "");

        if (!/^\d{11}$|^\d{14}$/.test(cnpj)) {
            alert("Digite um CPF (11 dígitos) ou CNPJ (14 dígitos) válido!");
            return;
        }

        mostrar(loader);
        ocultar(msgErro);
        ocultar(empresaDados);

        try {

            const formData = new FormData();
            formData.append("cnpj", cnpj);

            const response = await fetch("/identificar-empresa/", {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            ocultar(loader);

            if (data.success) {

                nomeEmpresa.textContent = data.empresa.nome;
                cnpjEmpresa.textContent = data.empresa.cnpj;

                mostrar(empresaDados);

                document.cookie = `empresa_token=${data.token}; path=/`;
                document.cookie = `empresa_cnpj=${data.empresa.cnpj}; path=/`;

                setTimeout(() => {
                    window.location.href = "/dashboard/";
                }, 1000);

            } else {

                msgErro.textContent = data.msg;
                mostrar(msgErro);

            }

        } catch (erro) {

            console.error(erro);

            ocultar(loader);

            msgErro.textContent = "Erro ao consultar empresa. Tente novamente.";

            mostrar(msgErro);

        }

    });

});