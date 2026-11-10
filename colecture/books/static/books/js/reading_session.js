/* Aba "Registrar leitura" (R18).
 *
 * De onde vêm os dados:
 *  - Status "Lendo": localStorage "colectureShelf" ({ idDoLivro: "reading" | "read" | ... }),
 *    o mesmo que o search.js grava.
 *  - Sessões: localStorage "colectureSessions" ({ idDoLivro: [sessão, ...] }).
 *  - Título/autor/páginas/capa: endpoint books:lookup (?ids=1,2,3).
 *
 * O progresso é guardado em percentual em cada sessão, assim registros por
 * páginas e por % podem ser misturados no mesmo livro.
 */
(function () {
  var root = document.getElementById('readingSession');
  if (!root) return;

  var SHELF_KEY = 'colectureShelf';
  var SESSIONS_KEY = 'colectureSessions';
  var MAX_MINUTES = 1440;
  var MINUTES_PER_PAGE = 2; // velocidade média usada quando o usuário não informa o tempo

  // ---------- Toast (F06) ----------
  // Único ponto que conversa com o toast do repositório. Se a função de lá
  // tiver outro nome ou outra ordem de parâmetros, ajuste só aqui.
  function notify(type, message) {
    if (typeof window.showToast === 'function') {
      window.showToast(type, message); // main/js/toast.js: showToast(type, title, description)
    } else {
      (type === 'error' ? console.error : console.log)('[toast ' + type + '] ' + message);
    }
  }

  // ---------- Elementos ----------
  function $(sel) { return root.querySelector(sel); }

  var el = {
    loading: $('[data-rs-loading]'),
    empty: $('[data-rs-empty]'),
    loadError: $('[data-rs-load-error]'),
    retry: $('[data-rs-retry]'),
    content: $('[data-rs-content]'),
    cover: $('[data-rs-cover]'),
    coverEmpty: $('[data-rs-cover-empty]'),
    title: $('[data-rs-title]'),
    author: $('[data-rs-author]'),
    genre: $('[data-rs-genre]'),
    pagesTotal: $('[data-rs-pages-total]'),
    history: $('[data-rs-history]'),
    historyEmpty: $('[data-rs-history-empty]'),
    historyOpen: $('[data-rs-history-open]'),
    historyModal: $('[data-rs-history-modal]'),
    historyClose: $('[data-rs-history-close]'),
    historyBook: $('[data-rs-history-book]'),
    clear: $('[data-rs-clear]'),
    percent: $('[data-rs-percent]'),
    bar: $('[data-rs-bar]'),
    fill: $('[data-rs-fill]'),
    preview: $('[data-rs-preview]'),
    detail: $('[data-rs-detail]'),
    eta: $('[data-rs-eta]'),
    finished: $('[data-rs-finished]'),
    markRead: $('[data-rs-mark-read]'),
    form: $('[data-rs-form]'),
    fields: $('[data-rs-fields]'),
    typePages: $('#rsTypePages'),
    typePercent: $('#rsTypePercent'),
    noPages: $('[data-rs-no-pages]'),
    amount: $('#rsAmount'),
    amountLabel: $('[data-rs-amount-label]'),
    suffix: $('[data-rs-suffix]'),
    remaining: $('[data-rs-remaining]'),
    amountError: $('#rsAmountError'),
    minutes: $('#rsMinutes'),
    minutesError: $('#rsMinutesError')
  };

  var lookupUrl = root.dataset.lookupUrl;
  // URLs com "0" no lugar do id do livro (preenchidas em bookUrl)
  var progressUrl = root.dataset.progressUrl;
  var markReadUrl = root.dataset.markReadUrl;
  var csrf = root.dataset.csrf;
  // Livro escolhido no card do perfil (?book=<id>): abre direto nele, sem seletor
  var requestedId = new URLSearchParams(window.location.search).get('book');
  var books = [];          // livros "Lendo" com dados do servidor
  var current = null;      // livro selecionado
  var triedSubmit = false; // só mostra erros "ao vivo" depois da 1ª tentativa

  // ---------- Armazenamento ----------
  function readStore(key) {
    try {
      var raw = localStorage.getItem(key);
      var data = raw ? JSON.parse(raw) : {};
      return data && typeof data === 'object' ? data : {};
    } catch (e) {
      return {};
    }
  }

  function writeStore(key, data) {
    localStorage.setItem(key, JSON.stringify(data)); 
    // Toda mudança nas sessões (registro ou edição) atualiza o progresso no banco
    if (key === SESSIONS_KEY && current) syncProgress(current);
  }

  // ---------- Banco de dados (estante do perfil) ----------
  function bookUrl(template, bookId) {
    return template.replace('/shelf/0/', '/shelf/' + encodeURIComponent(bookId) + '/');
  }

  function postJson(url, body) {
    return fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
      body: body ? JSON.stringify(body) : undefined
    }).then(function (res) {
      if (!res.ok) throw new Error('HTTP ' + res.status);
      return res.json();
    });
  }

  function syncProgress(book) {
    var percent = summaryOf(book).percent;
    postJson(bookUrl(progressUrl, book.id), { percent: percent }).catch(function () {
      notify('error', 'Não foi possível salvar o progresso na sua estante.');
    });
  }

function readingIds() {
  var shelf = readStore(SHELF_KEY);
  return Object.keys(shelf).filter(function (id) {
    return shelf[id] === 'READING' || shelf[id] === 'WANT_TO_READ';
  });
}

  function sessionsOf(bookId) {
    var all = readStore(SESSIONS_KEY);
    return Array.isArray(all[bookId]) ? all[bookId] : [];
  }

  function saveSession(bookId, session) {
    var all = readStore(SESSIONS_KEY);
    if (!Array.isArray(all[bookId])) all[bookId] = [];
    all[bookId].push(session);
    writeStore(SESSIONS_KEY, all);
  }


  function summaryOf(book) {
    var list = sessionsOf(book.id);
    var percent = 0, timedPercent = 0, minutes = 0;

    list.forEach(function (s) {
      var p = Number(s.percent) || 0;
      percent += p;
      if (s.minutes > 0) { minutes += s.minutes; timedPercent += p; }
    });

    percent = Math.min(100, Math.round(percent * 1000) / 1000);
    if (percent > 99.999) percent = 100;

    var pagesRead = book.pages ? Math.min(book.pages, Math.round(percent * book.pages / 100)) : null;

    var eta = null;
    if (minutes > 0 && timedPercent > 0) {
      eta = Math.max(0, Math.round((100 - percent) * minutes / timedPercent));
    } else if (book.pages) {
      eta = Math.max(0, Math.round(book.pages * (100 - percent) / 100 * MINUTES_PER_PAGE));
    }

    return { percent: percent, pagesRead: pagesRead, count: list.length, eta: eta };
  }

  function formatPercent(p) {
    return Math.floor(p) + '%';
  }

  function formatMinutes(total) {
    if (total < 1) return 'menos de 1 min';
    var h = Math.floor(total / 60);
    var m = total % 60;
    if (!h) return '~' + m + ' min';
    return h + ' h' + (m ? ' ' + m + ' min' : '');
  }

  function currentType() {
    return el.typePercent.checked ? 'percent' : 'pages';
  }

  function resetForm() {
    var type = currentType();
    el.form.reset();
    (type === 'percent' ? el.typePercent : el.typePages).checked = true;
    triedSubmit = false;
    clearErrors();
  }

  function remainingFor(book, sum, type) {
    if (type === 'pages') return book.pages - sum.pagesRead;
    return 100 - Math.floor(sum.percent);
  }

  function sessionPercent(book, sum, type, amount) {
    if (type === 'pages') {
      return ((sum.pagesRead + amount) / book.pages) * 100 - sum.percent;
    }
    return amount;
  }

  function parseNumber(input) {
    var v = input.value.trim().replace(',', '.');
    return v === '' ? null : Number(v);
  }

  function validateAmount() {
    var type = currentType();
    var sum = summaryOf(current);
    var value = parseNumber(el.amount);
    var msg = '';

    if (type === 'pages') {
      if (value === null || isNaN(value)) {
        msg = 'Informe em qual página você parou.';
      } else if (!Number.isInteger(value) || value <= 0) {
        msg = 'Use um número inteiro de página.';
      } else if (value > current.pages) {
        msg = 'Este livro tem ' + current.pages + ' páginas.';
      }
      setError(el.amount, el.amountError, msg);
      return msg ? null : value - sum.pagesRead;
    }

    // por percentual o campo é o percentual em que você está (não o quanto leu hoje)
    if (value === null || isNaN(value)) {
      msg = 'Informe em qual percentual do livro você está.';
    } else if (!Number.isInteger(value) || value <= 0) {
      msg = 'Use um número inteiro de percentual (ex.: 12).';
    } else if (value > 100) {
      msg = 'O percentual vai até 100%.';
    }

    setError(el.amount, el.amountError, msg);
    return msg ? null : value - sum.percent;
  }


  function maskDuration(value) {
    var d = value.replace(/\D/g, '').replace(/^0+(?=\d{3})/, '').slice(0, 4);
    return d.length > 2 ? d.slice(0, -2) + ':' + d.slice(-2) : d;
  }

  // Lê o tempo no formato "h:mm" (ou só minutos). Vazio = 0.
  // Retorna { total: minutos, msg: mensagem de erro ou '' }.
  function parseDuration(raw) {
    raw = (raw || '').trim();
    var msg = '';
    var total = 0;

    if (raw !== '') {
      var match = raw.match(/^(\d{1,2}):(\d{2})$/) || raw.match(/^()(\d{1,2})$/);
      if (!match) {
        msg = 'Use o formato h:mm (ex.: 1:30) ou só os minutos (ex.: 45).';
      } else {
        var h = Number(match[1] || 0);
        var m = Number(match[2]);
        total = h * 60 + m;
        if (match[1] && m > 59) msg = 'Os minutos vão de 00 a 59 (ex.: 1:30).';
        else if (total <= 0) msg = 'O tempo da sessão precisa ser maior que zero.';
        else if (total > MAX_MINUTES) msg = 'Uma sessão pode ter no máximo 24:00.';
      }
    }

    return { total: total, msg: msg };
  }

  function validateMinutes() {
    var result = parseDuration(el.minutes.value);
    setError(el.minutes, el.minutesError, result.msg);
    return result.msg ? false : result.total;
  }

  // Ex.: 90 -> "1:30" (usado para preencher o campo na edição)
  function formatHM(total) {
    return Math.floor(total / 60) + ':' + pad2(total % 60);
  }

  function formatDuration(total) {
    var h = Math.floor(total / 60);
    var m = total % 60;
    if (!h) return m + ' min';
    return h + ' h' + (m ? ' ' + m + ' min' : '');
  }

  function setError(input, box, msg) {
    box.textContent = msg;
    box.hidden = !msg;
    if (msg) input.setAttribute('aria-invalid', 'true');
    else input.removeAttribute('aria-invalid');
  }

  function clearErrors() {
    setError(el.amount, el.amountError, '');
    setError(el.minutes, el.minutesError, '');
  }

  // ---------- Renderização ----------
  function renderTypeUI() {
    var hasPages = !!current.pages;
    el.typePages.disabled = !hasPages;
    el.noPages.hidden = hasPages;
    if (!hasPages) el.typePercent.checked = true;

    var type = currentType();
    var sum = summaryOf(current);
    var remaining = remainingFor(current, sum, type);

    if (type === 'pages') {
      el.amountLabel.textContent = 'Em qual página você parou? ';
      el.suffix.textContent = 'pág.';
      el.amount.step = '1';
      el.amount.min = '1'; // pode registrar uma página menor que a atual
      el.amount.max = String(current.pages);
      el.amount.setAttribute('inputmode', 'numeric');
      el.remaining.textContent = sum.pagesRead
        ? 'Restam ' + remaining + ' páginas para finalizar o livro.'
        : 'Você ainda não registrou nenhuma página (total: ' + current.pages + ').';
    } else {
      el.amountLabel.textContent = 'Em qual percentual do livro você está?';
      el.suffix.textContent = '%';
      el.amount.step = '1';
      el.amount.min = '1';
      el.amount.max = '100';
      el.amount.setAttribute('inputmode', 'numeric');
      el.remaining.textContent = 'Restam ' + formatPercent(remaining) +
        (current.pages ? ' (' + (current.pages - sum.pagesRead) + ' pág.)' : '') +
        ' para concluir o livro.';
    }
  }

  function renderSummary() {
    var sum = summaryOf(current);
    var done = sum.percent >= 100;

    el.title.textContent = current.title;
    el.author.textContent = current.author || '';
    el.genre.textContent = current.genre || '';
    el.genre.hidden = !current.genre;
    el.pagesTotal.textContent = current.pages ? '• ' + current.pages + ' páginas no total' : '';

    if (current.icon) {
      el.cover.src = current.icon;
      el.cover.alt = 'Capa de ' + current.title;
      el.cover.hidden = false;
      el.coverEmpty.hidden = true;
    } else {
      el.cover.hidden = true;
      el.coverEmpty.hidden = false;
    }

    el.percent.textContent = formatPercent(sum.percent);
    el.fill.style.width = sum.percent + '%';
    el.bar.setAttribute('aria-valuenow', String(Math.floor(sum.percent)));
    el.bar.classList.toggle('is-complete', done);

    el.detail.textContent = current.pages
      ? sum.pagesRead + ' de ' + current.pages + ' páginas lidas'
      : 'Livro sem número de páginas cadastrado';

    if (done) {
      el.eta.textContent = 'Leitura concluída!';
      el.eta.classList.remove('is-muted');
    } else if (sum.eta === null) {
      // só acontece em livro sem número de páginas e sem nenhuma sessão com tempo
      el.eta.textContent = 'Informe o tempo de uma sessão para calcular';
      el.eta.classList.add('is-muted');
    } else {
      el.eta.textContent = formatMinutes(sum.eta);
      el.eta.classList.remove('is-muted');
    }


    el.finished.hidden = !done;
    el.fields.disabled = done;

    renderPreview();
    renderHistory();
  }

  // ---------- Histórico (pop-up) ----------
  var MONTHS = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
  var editingIndex = null; // registro sendo editado (índice na lista cronológica)

  function pad2(n) { return (n < 10 ? '0' : '') + n; }

  // Ex.: "08/nov/2026 15:00"
  function formatDateTime(iso) {
    var d = new Date(iso);
    if (isNaN(d)) return '';
    return pad2(d.getDate()) + '/' + MONTHS[d.getMonth()] + '/' + d.getFullYear() +
      ' ' + pad2(d.getHours()) + ':' + pad2(d.getMinutes());
  }

  // Progresso acumulado ao fim de cada sessão (ordem cronológica): { percent, pages }
  function timelineOf(book, list) {
    var cum = 0;
    return list.map(function (s) {
      cum = Math.min(100, cum + (Number(s.percent) || 0));
      var pages = null;
      if (book.pages) {
        pages = (s.type === 'pages' && s.page) ? s.page : Math.min(book.pages, Math.round(cum * book.pages / 100));
      }
      return { percent: cum, pages: pages };
    });
  }

  // Recalcula a quantidade lida (amount) do registro j depois de uma edição
  function refreshAmount(book, list, j) {
    var tl = timelineOf(book, list);
    var s = list[j];
    if (s.type === 'pages' && book.pages) {
      s.amount = tl[j].pages - (j > 0 ? tl[j - 1].pages : 0);
    } else {
      s.amount = Math.round(Number(s.percent) || 0);
    }
  }

  function writeSessions(bookId, list) {
    var all = readStore(SESSIONS_KEY);
    all[bookId] = list;
    writeStore(SESSIONS_KEY, all);
  }

  // Lista do pop-up (mais recente primeiro)
  function renderHistory() {
    var list = sessionsOf(current.id);
    var tl = timelineOf(current, list);

    el.historyBook.textContent = current.title;
    el.history.innerHTML = '';
    el.historyEmpty.hidden = list.length > 0;

    for (var i = list.length - 1; i >= 0; i--) {
      if (i === editingIndex) el.history.appendChild(editItem(list, tl, i));
      else el.history.appendChild(historyItem(list[i], tl, i));
    }
  }

  // Ex.: "263/433 pág. (60%)" + "08/nov/2026 15:00 · +32 págs · 1 h 30 min"
  function historyItem(s, tl, i) {
    var li = document.createElement('li');
    li.className = 'rs-history-item';
    li.dataset.index = i;

    var text = document.createElement('div');
    text.className = 'rs-history-text';

    var title = document.createElement('strong');
    title.textContent = current.pages
      ? tl[i].pages + '/' + current.pages + ' pág. (' + formatPercent(tl[i].percent) + ')'
      : formatPercent(tl[i].percent);

    // Pode ser negativo se a atualização foi editada para uma página menor que a anterior
    var diff = current.pages
      ? tl[i].pages - (i > 0 ? tl[i - 1].pages : 0)
      : Math.round(Number(s.percent) || 0);
    var read = (diff < 0 ? '−' : '+') + Math.abs(diff) + (current.pages ? ' págs' : '%');

    var meta = document.createElement('span');
    meta.textContent = [formatDateTime(s.date), read, s.minutes ? formatDuration(s.minutes) : '']
      .filter(Boolean).join(' · ');

    text.appendChild(title);
    text.appendChild(meta);

    // Menu ⋮ (conteúdo fixo, sem dados do usuário)
    var menu = document.createElement('div');
    menu.className = 'rs-menu';
    menu.innerHTML =
      '<button type="button" class="rs-icon-btn" data-action="menu" aria-haspopup="menu" aria-expanded="false" aria-label="Opções da atualização">' +
        '<i class="bx bx-dots-vertical-rounded" aria-hidden="true"></i></button>' +
      '<div class="rs-menu-list" role="menu" hidden>' +
        '<button type="button" role="menuitem" data-action="edit"><i class="bx bx-edit-alt" aria-hidden="true"></i> Editar atualização</button>' +
      '</div>';

    li.appendChild(text);
    li.appendChild(menu);
    return li;
  }

  // Formulário de edição dentro do próprio item
  function editItem(list, tl, i) {
    var s = list[i];
    var byPages = s.type === 'pages' && !!current.pages;

    var li = document.createElement('li');
    li.className = 'rs-history-item rs-history-item--form';
    li.dataset.index = i;
    li.innerHTML =
      '<form class="rs-edit" novalidate>' +
        '<div class="rs-edit-grid">' +
          '<div>' +
            '<label for="rsEditAmount">' + (byPages ? 'Página em que parou' : 'Percentual em que parou') + '</label>' +
            '<div class="rs-input-group">' +
              '<input id="rsEditAmount" name="amount" class="rs-input" type="number" inputmode="numeric" min="1" step="1" />' +
              '<span class="rs-addon" aria-hidden="true">' + (byPages ? 'pág.' : '%') + '</span>' +
            '</div>' +
          '</div>' +
          '<div>' +
            '<label for="rsEditDuration">Tempo da sessão</label>' +
            '<div class="rs-input-group">' +
              '<input id="rsEditDuration" name="duration" class="rs-input" type="text" inputmode="numeric" maxlength="5" placeholder="Ex.: 1:30" autocomplete="off" />' +
              '<span class="rs-addon" aria-hidden="true">h:min</span>' +
            '</div>' +
          '</div>' +
        '</div>' +
        '<p class="rs-error" role="alert" hidden></p>' +
        '<div class="rs-edit-actions">' +
          '<button type="button" class="rs-btn" data-action="cancel">Cancelar</button>' +
          '<button type="submit" class="rs-btn rs-btn--primary">Salvar</button>' +
        '</div>' +
      '</form>';

    var form = li.querySelector('form');
    form.elements.amount.value = byPages ? tl[i].pages : Math.round(tl[i].percent);
    form.elements.duration.value = s.minutes ? formatHM(s.minutes) : '';
    return li;
  }

  // Salva a edição: o registro seguinte é ajustado para manter o progresso dele
  function saveEdit(i, form) {
    var list = sessionsOf(current.id);
    var tl = timelineOf(current, list);
    var s = list[i];
    if (!s) return;

    var byPages = s.type === 'pages' && !!current.pages;
    var prev = i > 0 ? tl[i - 1] : { percent: 0, pages: 0 };
    var next = i < list.length - 1 ? tl[i + 1] : null;
    var raw = form.elements.amount.value.trim();
    var value = Number(raw);
    var msg = '';
    var newCum = 0;

    if (raw === '' || isNaN(value) || !Number.isInteger(value) || value <= 0) {
      msg = byPages ? 'Informe a página em que parou (número inteiro).' : 'Informe o percentual como número inteiro maior que zero.';
    } else if (byPages) {
      // Pode ser qualquer página do livro, inclusive menor que a da atualização anterior
      if (value > current.pages) msg = 'Este livro tem ' + current.pages + ' páginas.';
      newCum = value === current.pages ? 100 : value / current.pages * 100;
    } else {
      // Percentual em que parou (acumulado), não o quanto leu na sessão
      if (value > 100) msg = 'O percentual vai até 100%.';
      newCum = value;
    }

    var dur = parseDuration(form.elements.duration.value);
    if (!msg) msg = dur.msg;

    if (msg) {
      var box = form.querySelector('.rs-error');
      box.textContent = msg;
      box.hidden = false;
      return;
    }

    s.percent = newCum - prev.percent;
    if (byPages) s.page = value;
    s.minutes = dur.total || null;
    if (next) list[i + 1].percent = next.percent - newCum;

    refreshAmount(current, list, i);
    if (next) refreshAmount(current, list, i + 1);

    try {
      writeSessions(current.id, list);
    } catch (err) {
      notify('error', 'Não foi possível salvar a edição. Tente de novo.');
      return;
    }

    editingIndex = null;
    renderTypeUI();
    renderSummary();
    notify('success', 'Atualização editada.');
  }

  function closeMenus() {
    root.querySelectorAll('.rs-menu-list').forEach(function (m) { m.hidden = true; });
    root.querySelectorAll('[data-action="menu"]').forEach(function (b) { b.setAttribute('aria-expanded', 'false'); });
  }

  function toggleMenu(btn) {
    var list = btn.nextElementSibling;
    var willOpen = list.hidden;
    closeMenus();
    if (willOpen) {
      list.hidden = false;
      btn.setAttribute('aria-expanded', 'true');
      list.querySelector('button').focus();
    }
  }

  // Faixa listrada mostrando o que a sessão digitada vai somar
  function renderPreview() {
    var sum = summaryOf(current);
    var value = parseNumber(el.amount);
    var add = 0;
    var type = currentType();

    // por páginas o campo é a página onde parou -> converte para páginas lidas
    // por % o campo é o percentual atual -> converte para o percentual lido na sessão
    if (type === 'pages' && value !== null) value = value - sum.pagesRead;
    else if (type === 'percent' && value !== null) value = value - sum.percent;

    if (value !== null && !isNaN(value) && value > 0 && value <= remainingFor(current, sum, type)) {
      add = Math.max(0, sessionPercent(current, sum, type, value));
    }

    el.preview.style.left = sum.percent + '%';
    el.preview.style.width = Math.min(add, 100 - sum.percent) + '%';
  }

  function renderAll() {
    renderTypeUI();
    renderSummary();
  }

  function show(state) {
    el.loading.hidden = state !== 'loading';
    el.empty.hidden = state !== 'empty';
    el.loadError.hidden = state !== 'error';
    el.content.hidden = state !== 'content';
  }

  // ---------- Carregamento ----------
  function load() {
    var ids = readingIds();
    if (requestedId && /^\d+$/.test(requestedId) && ids.indexOf(requestedId) === -1) ids.push(requestedId);
    if (!ids.length) { books = []; show('empty'); return; }

    show('loading');

    fetch(lookupUrl + '?ids=' + encodeURIComponent(ids.join(',')), {
      headers: { 'Accept': 'application/json' },
      credentials: 'same-origin'
    })
      .then(function (res) {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
      })
      .then(function (data) {
        // Mantém só os que continuam "Lendo" e existem no banco
        books = (data.results || []).map(function (b) {
          return { id: String(b.id), title: b.title, author: b.author, genre: b.genre || '', pages: b.pages || null, icon: b.icon || '' };
        });

        if (!books.length) { show('empty'); return; }

        var keep = current && books.some(function (b) { return b.id === current.id; });
        current = (keep ? findBook(current.id) : findBook(requestedId)) || books[0];
        show('content');
        renderAll();
        // Leva para o banco sessões já registradas antes (só se houver alguma)
        if (summaryOf(current).count) syncProgress(current);
      })
      .catch(function () {
        show('error');
        notify('error', 'Não foi possível carregar seus livros em leitura.');
      });
  }

  function findBook(id) {
    for (var i = 0; i < books.length; i++) if (books[i].id === String(id)) return books[i];
    return null;
  }

  // ---------- Eventos ----------

  // F02: troca páginas ↔ %
  [el.typePages, el.typePercent].forEach(function (radio) {
    radio.addEventListener('change', function () {
      el.amount.value = '';
      clearErrors();
      renderTypeUI();
      renderPreview();
    });
  });

  // Botão "Limpar" do cabeçalho do formulário
  el.clear.addEventListener('click', function () {
    resetForm();
    renderTypeUI();
    renderPreview();
    el.amount.focus();
  });

  el.amount.addEventListener('input', function () {
    if (triedSubmit) validateAmount();
    renderPreview();
  });

  el.minutes.addEventListener('input', function () {
    el.minutes.value = maskDuration(el.minutes.value);
    if (triedSubmit) validateMinutes();
  });

  el.form.addEventListener('submit', function (e) {
    e.preventDefault();
    triedSubmit = true;

    var amount = validateAmount();
    var minutes = validateMinutes();

    if (amount === null || minutes === false) {
      (amount === null ? el.amount : el.minutes).focus();
      notify('error', 'Confira os campos destacados antes de registrar.');
      return;
    }

    // Garante que o livro ainda está como "Lendo" (pode ter mudado em outra aba)
    if (readingIds().indexOf(current.id) === -1) {
      notify('error', 'Este livro não está mais marcado como “Lendo”.');
      load();
      return;
    }

    var type = currentType();
    var sum = summaryOf(current);
    var session = {
      date: new Date().toISOString(),
      type: type,
      amount: amount, // páginas lidas na sessão (ou %)
      page: type === 'pages' ? sum.pagesRead + amount : null, // página onde parou
      percent: sessionPercent(current, sum, type, amount),
      minutes: minutes || null
    };

    try {
      saveSession(current.id, session);
    } catch (err) {
      notify('error', 'Não foi possível salvar a sessão. Verifique o armazenamento do navegador e tente de novo.');
      return;
    }

    resetForm();
    renderTypeUI();
    renderSummary();

    var after = summaryOf(current);
    if (after.percent >= 100) {
      notify('success', 'Sessão registrada! Você chegou a 100%.');
      el.finished.focus();
    } else {
      notify('success', 'Sessão registrada! Você está em ' + formatPercent(after.percent) + '.');
    }
  });

  // Sugestão ao chegar em 100%
  el.markRead.addEventListener('click', function () {
    var book = current;
    el.markRead.disabled = true;

    // Salva no banco (status Lido + data de conclusão) e depois no localStorage
    postJson(bookUrl(markReadUrl, book.id))
      .then(function () {
        var shelf = readStore(SHELF_KEY);
        shelf[book.id] = 'READ';
        writeStore(SHELF_KEY, shelf);

        notify('success', '“' + book.title + '” foi marcado como lido.');
        books = books.filter(function (b) { return b.id !== book.id; });

        if (!books.length) { show('empty'); return; }
        current = books[0];
        renderAll();
      })
      .catch(function () {
        notify('error', 'Não foi possível marcar o livro como lido. Tente de novo.');
      })
      .then(function () { el.markRead.disabled = false; });
  });

  // ---------- Pop-up do histórico ----------
  el.historyOpen.addEventListener('click', function () {
    editingIndex = null;
    renderHistory();
    el.historyModal.showModal();
  });

  el.historyClose.addEventListener('click', function () { el.historyModal.close(); });

  // Clique fora da caixa (no fundo escuro) fecha
  el.historyModal.addEventListener('click', function (e) {
    if (e.target === el.historyModal) el.historyModal.close();
  });

  // Esc: se houver menu aberto, fecha só o menu
  el.historyModal.addEventListener('cancel', function (e) {
    if (root.querySelector('.rs-menu-list:not([hidden])')) {
      e.preventDefault();
      closeMenus();
    }
  });

  el.historyModal.addEventListener('close', function () {
    editingIndex = null;
    closeMenus();
  });

  // Ações dos itens (menu ⋮, editar, excluir, cancelar)
  el.history.addEventListener('click', function (e) {
    var btn = e.target.closest('button');
    if (!btn) return;
    var item = btn.closest('[data-index]');
    var i = item ? Number(item.dataset.index) : null;
    var action = btn.dataset.action;

    if (action === 'menu') { toggleMenu(btn); return; }
    closeMenus();

    if (action === 'edit') {
      editingIndex = i;
      renderHistory();
      el.history.querySelector('#rsEditAmount').focus();
    } else if (action === 'cancel') {
      editingIndex = null;
      renderHistory();
    }
  });

  el.history.addEventListener('submit', function (e) {
    e.preventDefault();
    var item = e.target.closest('[data-index]');
    if (item) saveEdit(Number(item.dataset.index), e.target);
  });

  // Máscara h:mm também no campo de tempo da edição
  el.history.addEventListener('input', function (e) {
    if (e.target.name === 'duration') e.target.value = maskDuration(e.target.value);
  });

  // Clique fora de um menu ⋮ fecha os menus
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.rs-menu')) closeMenus();
  });

  el.retry.addEventListener('click', load);

  // Se o status mudar em outra aba do navegador, recarrega
  window.addEventListener('storage', function (e) {
    if (e.key === SHELF_KEY) load();
    if (e.key === SESSIONS_KEY && current) { renderTypeUI(); renderSummary(); }
  });

  load();
})();