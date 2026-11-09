/**
 * Estante do perfil ("Sua estante").
 *  - Filtro por status sem recarregar a página (+ estado vazio por filtro);
 *  - Clicar no card em Lendo / Quero ler abre o registro de progresso
 *    (Quero ler passa para Lendo); em Lido abre a página do livro;
 *  - Tag clicável abre o pop-up "Alterar estante" para trocar a tag a qualquer momento;
 *  - Contadores, card e toast (showToast de main/js/toast.js) atualizados após cada mudança.
 */
(function () {
  'use strict';

  var shelf = document.querySelector('[data-shelf]');
  if (!shelf) return;

  var grid = shelf.querySelector('[data-shelf-grid]');
  if (!grid) return; // estante totalmente vazia: só o texto padrão

  var emptyMsg = shelf.querySelector('[data-shelf-empty]');
  var filterButtons = shelf.querySelectorAll('[data-shelf-filter]');
  var csrf = shelf.getAttribute('data-csrf');
  var shelfUrl = shelf.getAttribute('data-shelf-url');
  var progressUrl = shelf.getAttribute('data-progress-url');

  // A tela de registrar leitura lê os status do localStorage (mesma chave da pesquisa)
  var SHELF_STORAGE_KEY = 'colectureShelf';

  var LABELS = { READ: 'Lido', READING: 'Lendo', WANT_TO_READ: 'Quero ler' };
  var activeFilter = 'ALL';

  function cards() {
    return Array.prototype.slice.call(grid.querySelectorAll('[data-shelf-book]'));
  }

  function toast(type, title, desc) {
    if (typeof window.showToast === 'function') window.showToast(type, title, desc);
  }

  function syncLocalShelf() {
    var data = {};
    cards().forEach(function (card) {
      data[card.getAttribute('data-book-id')] = card.getAttribute('data-status');
    });
    try { localStorage.setItem(SHELF_STORAGE_KEY, JSON.stringify(data)); } catch (e) {}
  }

  // ---------- Requisições ----------
  function postJson(url, body) {
    return fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf,
        'X-Requested-With': 'XMLHttpRequest',
      },
      body: body ? JSON.stringify(body) : undefined,
    }).then(function (res) {
      return res.json().catch(function () { return {}; }).then(function (data) {
        if (!res.ok || !data.success) throw new Error(data.error || 'Tente novamente em instantes.');
        return data;
      });
    });
  }

  // Lido usa o endpoint próprio (salva data de conclusão e progresso 100%)
  function saveStatus(card, status) {
    if (status === 'READ') return postJson(card.getAttribute('data-mark-url'));
    return postJson(shelfUrl, { book_id: Number(card.getAttribute('data-book-id')), status: status });
  }

  function errorMessage(err) {
    return err instanceof TypeError ? 'Verifique sua conexão e tente de novo.' : err.message;
  }

  // ---------- Filtro ----------
  function applyFilter(value) {
    activeFilter = value;

    filterButtons.forEach(function (btn) {
      var isActive = btn.getAttribute('data-shelf-filter') === value;
      btn.classList.toggle('is-active', isActive);
      btn.setAttribute('aria-pressed', isActive ? 'true' : 'false');
    });

    var all = cards();
    var visible = 0;
    all.forEach(function (card) {
      var show = value === 'ALL' || card.getAttribute('data-status') === value;
      card.hidden = !show;
      if (show) visible++;
    });

    grid.hidden = visible === 0;
    emptyMsg.hidden = visible !== 0;
    emptyMsg.textContent = (value === 'ALL' || all.length === 0)
      ? 'Você ainda não registrou nenhum livro.'
      : 'Você ainda não tem livros em ' + LABELS[value] + '.';
  }

  function updateCounts() {
    var counts = { ALL: 0 };
    cards().forEach(function (card) {
      var status = card.getAttribute('data-status');
      counts[status] = (counts[status] || 0) + 1;
      counts.ALL++;
    });
    shelf.querySelectorAll('[data-shelf-count]').forEach(function (el) {
      el.textContent = counts[el.getAttribute('data-shelf-count')] || 0;
    });
  }

  function refreshShelf() {
    updateCounts();
    applyFilter(activeFilter);
    syncLocalShelf();
  }

  // ---------- Card ----------
  function buildProgress(card) {
    var percent = Number(card.getAttribute('data-progress')) || 0;
    var pages = card.getAttribute('data-pages');
    var pagesRead = card.getAttribute('data-pages-read') || '0';

    var wrap = document.createElement('div');
    wrap.className = 'shelf-progress';
    wrap.setAttribute('data-shelf-progress', '');
    wrap.innerHTML =
      '<div class="shelf-progress__bar" role="progressbar" aria-valuemin="0" aria-valuemax="100"' +
      ' aria-label="Progresso de leitura"><span></span></div>' +
      '<span class="shelf-progress__text"></span>';
    wrap.querySelector('.shelf-progress__bar').setAttribute('aria-valuenow', percent);
    wrap.querySelector('.shelf-progress__bar span').style.width = percent + '%';
    wrap.querySelector('.shelf-progress__text').textContent =
      (pages ? pagesRead + '/' + pages + ' pág. · ' : '') + percent + '%';
    return wrap;
  }

  // Ajusta o card para a nova tag (progresso só em Lendo)
  function renderCard(card, status, data) {
    card.setAttribute('data-status', status);
    if (data && typeof data.progress === 'number') {
      card.setAttribute('data-progress', data.progress);
      var pages = card.getAttribute('data-pages');
      if (pages) card.setAttribute('data-pages-read', Math.round(data.progress / 100 * Number(pages)));
    }

    var title = card.getAttribute('data-book-title');
    var tag = card.querySelector('[data-shelf-tag]');
    tag.className = 'shelf-book__tag shelf-book__tag--' + status.toLowerCase();
    tag.querySelector('[data-shelf-tag-label]').textContent = LABELS[status];
    tag.setAttribute('aria-label', 'Alterar tag de ' + title + ' (atual: ' + LABELS[status] + ')');

    var body = card.querySelector('.shelf-book__body');
    var progress = card.querySelector('[data-shelf-progress]');
    if (progress) progress.remove();
    if (status === 'READING') body.appendChild(buildProgress(card));
  }

  // Abre a tela de registrar leitura já no livro clicado
  function progressPageFor(card) {
    return progressUrl + '?book=' + encodeURIComponent(card.getAttribute('data-book-id'));
  }

  // ---------- Clique no card ----------
  // Lendo / Quero ler: registro de progresso. Lido: página do livro.
  function openCard(card) {
    var status = card.getAttribute('data-status');

    if (status === 'READ') {
      window.location.href = card.getAttribute('data-detail-url');
      return;
    }

    if (status === 'READING') {
      syncLocalShelf();
      window.location.href = progressPageFor(card);
      return;
    }

    // Quero ler: a tela de registro só lista livros em Lendo
    saveStatus(card, 'READING')
      .then(function () {
        renderCard(card, 'READING');
        refreshShelf();
        window.location.href = progressPageFor(card);
      })
      .catch(function (err) {
        toast('error', 'Não foi possível abrir o registro de progresso', errorMessage(err));
      });
  }

  // ---------- Pop-up "Alterar estante" ----------
  var modal = document.querySelector('[data-status-modal]');
  var modalBook = modal.querySelector('[data-modal-book]');
  var modalSave = modal.querySelector('[data-modal-save]');
  var modalOptions = modal.querySelectorAll('[data-modal-option]');
  var modalCard = null;
  var selected = '';
  var lastFocus = null;

  function refreshModal() {
    modalOptions.forEach(function (opt) {
      var isSel = opt.getAttribute('data-modal-option') === selected;
      opt.classList.toggle('selected', isSel);
      opt.setAttribute('aria-pressed', isSel ? 'true' : 'false');
    });
    modalSave.disabled = !selected || selected === modalCard.getAttribute('data-status');
  }

  function openModal(card) {
    modalCard = card;
    selected = card.getAttribute('data-status');
    modalBook.textContent = card.getAttribute('data-book-title');
    lastFocus = document.activeElement;
    refreshModal();
    modal.hidden = false;
    modal.querySelector('.modal-option.selected').focus();
  }

  function closeModal() {
    modal.hidden = true;
    modalCard = null;
    if (lastFocus) lastFocus.focus();
  }

  function setBusy(busy) {
    modal.querySelectorAll('button').forEach(function (b) { b.disabled = busy; });
    if (!busy) refreshModal();
  }

  modalOptions.forEach(function (opt) {
    opt.addEventListener('click', function () {
      selected = opt.getAttribute('data-modal-option');
      refreshModal();
    });
  });

  modal.querySelectorAll('[data-modal-close]').forEach(function (b) {
    b.addEventListener('click', closeModal);
  });

  modal.addEventListener('click', function (e) {
    if (e.target === modal) closeModal();
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !modal.hidden) closeModal();
  });

  modalSave.addEventListener('click', function () {
    var card = modalCard;
    var status = selected;
    var title = card.getAttribute('data-book-title');

    setBusy(true);
    saveStatus(card, status)
      .then(function (data) {
        renderCard(card, status, data);
        refreshShelf();
        setBusy(false);
        closeModal();
        toast('success', 'Estante atualizada!', title + ' foi movido para ' + LABELS[status] + '.');
      })
      .catch(function (err) {
        setBusy(false);
        toast('error', 'Não foi possível alterar a estante', errorMessage(err));
      });
  });

  modal.querySelector('[data-modal-remove]').addEventListener('click', function () {
    var card = modalCard;
    var title = card.getAttribute('data-book-title');

    setBusy(true);
    postJson(shelfUrl, { book_id: Number(card.getAttribute('data-book-id')), status: null })
      .then(function () {
        setBusy(false);
        lastFocus = null;
        closeModal();
        card.remove();
        refreshShelf();
        toast('success', 'Livro removido da estante', title + ' saiu da sua lista.');
      })
      .catch(function (err) {
        setBusy(false);
        toast('error', 'Não foi possível remover o livro', errorMessage(err));
      });
  });

  // ---------- Eventos ----------
  filterButtons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      applyFilter(btn.getAttribute('data-shelf-filter'));
    });
  });

  grid.addEventListener('click', function (event) {
    var card = event.target.closest('[data-shelf-book]');
    if (!card) return;

    // A tag abre o pop-up; o resto do card abre o livro
    if (event.target.closest('[data-change-status]')) {
      openModal(card);
      return;
    }
    openCard(card);
  });

  // Teclado: Enter / Espaço no card focado
  grid.addEventListener('keydown', function (event) {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    var card = event.target;
    if (!card.matches || !card.matches('[data-shelf-book]')) return;
    event.preventDefault();
    openCard(card);
  });

  // Voltando da tela de registrar leitura pelo "voltar" do navegador,
  // a página pode vir do cache: recarrega para mostrar o progresso novo.
  window.addEventListener('pageshow', function (event) {
    if (event.persisted) window.location.reload();
  });

  syncLocalShelf();
  applyFilter(activeFilter);
})();
