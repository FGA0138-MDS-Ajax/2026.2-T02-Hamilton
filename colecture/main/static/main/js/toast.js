
const TOAST_ICONS = {
  success: 'bx-check-circle',
  error: 'bx-error-circle',
  info: 'bx-info-circle',
  warning: 'bxs-hot',
};

function showToast(type, title, description = '', time = 4000) {
  let container = document.getElementById('toast-container');

  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.setAttribute('aria-live', 'polite');
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;
  toast.style.setProperty('--toast-time', `${time}ms`);

  toast.innerHTML = `
    <div class="toast__icon">
      <i class="bx ${TOAST_ICONS[type] || TOAST_ICONS.info}"></i>
    </div>

    <div class="toast__body">
      <strong class="toast__title"></strong>
      <span class="toast__desc"></span>
    </div>

    <button type="button" class="toast__close" aria-label="Fechar">
      <i class="bx bx-x"></i>
    </button>

    <div class="toast__bar"></div>
  `;

  // textContent evita injetar HTML vindo do usuário.
  toast.querySelector('.toast__title').textContent = title;
  toast.querySelector('.toast__desc').textContent = description;

  const close = () => {
    if (toast.classList.contains('toast--out')) {
      return;
    }

    toast.classList.add('toast--out');
    setTimeout(() => toast.remove(), 250);
  };

  toast.querySelector('.toast__close').addEventListener('click', close);

  setTimeout(close, time);

  container.appendChild(toast);
}