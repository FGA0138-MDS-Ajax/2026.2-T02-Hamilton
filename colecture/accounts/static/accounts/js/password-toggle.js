// Mostra/oculta a senha nos campos que possuem um botão .toggle-password
document.querySelectorAll('.toggle-password').forEach((button) => {
    const input = document.getElementById(button.dataset.target);
    const icon = button.querySelector('i');
    if (!input) return;

    button.addEventListener('click', () => {
        const isHidden = input.type === 'password';
        input.type = isHidden ? 'text' : 'password';
        icon.classList.toggle('bx-show', !isHidden);
        icon.classList.toggle('bx-hide', isHidden);
        button.setAttribute('aria-label', isHidden ? 'Ocultar senha' : 'Mostrar senha');
        button.setAttribute('aria-pressed', String(isHidden));
        input.focus();
    });
});
