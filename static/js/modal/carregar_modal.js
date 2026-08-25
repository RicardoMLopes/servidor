
/**
 * Exibe um modal dinâmico e retorna uma Promise com a decisão do usuário.
 *
 * @param {Object} opcoes
 * @param {string} opcoes.titulo - Título do Modal (Padrão: "Aviso")
 * @param {string} opcoes.mensagem - Mensagem do Modal
 * @param {Array} opcoes.botoes - Lista de botões [{ texto, valor, classe }]
 * @returns {Promise<any>} Retorna o valor associado ao botão clicado
 */
function mostrarModal({ titulo = "Aviso", mensagem = "", botoes = [] }) {
    return new Promise((resolve) => {
        const modal = document.getElementById('modalGenerico');
        const elTitulo = document.getElementById('modalTitulo');
        const elMensagem = document.getElementById('modalMensagem');
        const elBotoes = document.getElementById('modalBotoes');

        elTitulo.textContent = titulo;
        elMensagem.textContent = mensagem;
        elBotoes.innerHTML = ''; // Limpa botões anteriores

        // Se nenhum botão for passado, cria um padrão "OK"
        if (botoes.length === 0) {
            botoes = [{ texto: 'OK', valor: true, classe: 'btn-primary' }];
        }

        botoes.forEach(btn => {
            const botaoEl = document.createElement('button');
            botaoEl.textContent = btn.texto;
            botaoEl.className = `btn-modal ${btn.classe || 'btn-primary'}`;

            botaoEl.onclick = () => {
                modal.classList.add('hidden'); // Fecha o modal
                resolve(btn.valor); // Retorna a resposta
            };

            elBotoes.appendChild(botaoEl);
        });

        modal.classList.remove('hidden'); // Exibe o modal
    });
}