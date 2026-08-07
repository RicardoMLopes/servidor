const container = document.getElementById('watermarks');
const cols = Math.ceil(window.innerWidth / 150);
const rows = Math.ceil(window.innerHeight / 70);

for (let i = 0; i < rows; i++) {
    for (let j = 0; j < cols; j++) {
        const span = document.createElement('span');
        const size = 14 + Math.random() * 12;
        const top = i * 60 + Math.random() * 20;
        const left = j * 130 + Math.random() * 40;
        const delay = Math.random() * 30;

        span.textContent = "DATA ACCESS";
        span.style.fontSize = `${size}px`;
        span.style.top = `${top}px`;
        span.style.left = `${left}px`;
        span.style.animationDelay = `${delay}s`;

        // CORREÇÃO CRUCIAL: Força cada span gerado a ignorar qualquer evento de mouse
        span.style.pointerEvents = 'none';

        container.appendChild(span);
    }
}