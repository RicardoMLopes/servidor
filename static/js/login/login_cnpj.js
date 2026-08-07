<script>
document.addEventListener("DOMContentLoaded", function() {
    const input = document.getElementById("cnpj");
    const form = document.getElementById("empresaForm");

    // Máscara adaptativa CPF / CNPJ
    input.addEventListener("input", function(e) {
        let value = e.target.value.replace(/\D/g, '');
        if(value.length <= 11){
            value = value.replace(/(\d{3})(\d)/, '$1.$2');
            value = value.replace(/(\d{3})\.(\d{3})(\d)/, '$1.$2.$3');
            value = value.replace(/(\d{3})\.(\d{3})\.(\d{3})(\d)/, '$1.$2.$3-$4');
        } else if(value.length <= 14){
            value = value.replace(/^(\d{2})(\d)/, '$1.$2');
            value = value.replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3');
            value = value.replace(/\.(\d{3})(\d)/, '.$1/$2');
            value = value.replace(/(\d{4})(\d)/, '$1-$2');
        }
        e.target.value = value;
    });

    form.addEventListener("submit", function(e) {
        input.value = input.value.replace(/\D/g, '');
    });
});
</script>