/* Aba "Registrar leitura" (R18).
 *
 * TUDO vem do servidor; este script não guarda nada no armazenamento do navegador:
 *  - Livros "Lendo":      GET  books:lookup                       (sem ?ids=)
 *  - Histórico/progresso: GET  books:list_reading_sessions        (sessões + book_status)
 *  - Criar sessão:        POST books:save_reading_session
 *  - Editar sessão:       PATCH books:edit_reading_session
 *  - Marcar como lido:    POST books:mark_book_as_read
 *
 * Cada ação chama o endpoint e re-renderiza com a RESPOSTA. Se a chamada falhar
 * (rede, sessão expirada, 400/404/5xx), a tela mostra o erro e nada é gravado em
 * lugar nenhum: o formulário continua preenchido para tentar de novo.
 */
(function () {
  var root = document.getElementById('readingSession');
  if (!root) return;

  var MAX_MINUTES = 1440;
  var MINUTES_PER_PAGE = 2; // velocidade média usada quando ainda não há sessões com tempo

  // ---------- Toast (F06) ----------
  // Único ponto que conversa com o toast do repositório (main/js/toast.js:
  // showToast(type, title, description)).
  function notify(type, message) {
    if (typeof window.showToast === 'function') {
      window.showToast(type, message);
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
    submit: $('[data-rs-form] button[type="submit"]'),
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

  // URLs com "0" no lugar do id do livro (e da sessão, na edição)
  var lookupUrl = root.dataset.lookupUrl;
  var sessionsUrl = root.dataset.sessionsUrl; // GET  /shelf/0/sessions/
  var sessionUrl = root.dataset.sessionUrl;   // POST /shelf/0/session/
  var editUrl = root.dataset.editUrl;         // PATCH /shelf/0/sessions/0/
  var markReadUrl = root.dataset.markReadUrl; // POST /shelf/0/mark-read/
  var csrf = root.dataset.csrf;

  // Livro escolhido no card do perfil (?book=<id>): abre direto nele, sem seletor
  var requestedId = new URLSearchParams(window.location.search).get('book');

  // ---------- Estado (só em memória, sempre vindo do servidor) ----------
  var books = [];          // livros "Lendo" (lookup)
  var current = null;      // livro selecionado
  var sessions = [];       // sessões do livro, da mais antiga para a mais recente
  var bookStatus = null;   // book_status devolvido pela API (ou null)
  var triedSubmit = false; // só mostra erros "ao vivo" depois da 1ª tentativa
  var editingId = null;    // id da sessão em edição no pop-up
  var busy = false;        // há uma gravação em andamento (evita duplo envio)
  var loadToken = 0;       // descarta respostas de carregamentos antigos

  // ---------- Chamadas à API ----------
  var MSG_NETWORK = 'Sem conexão com o servidor. Verifique sua internet e tente de novo. Nada foi salvo.';
  var MSG_AUTH = 'Sua sessão expirou. Recarregue a página e entre de novo. Nada foi salvo.';
  var MSG_UNCONFIRMED = 'Não foi possível confirmar a resposta do servidor. Recarregue a página para conferir seu histórico.';

  function apiError(message, extra) {
    var err = new Error(message);
    err.status = (extra && extra.status) || 0;
    err.field = (extra && extra.field) || '';
    err.network = !!(extra && extra.network);
    return err;
  }

  function bookUrl(template, bookId) {
    return template.replace('/shelf/0/', '/shelf/' + encodeURIComponent(bookId) + '/');
  }

  function sessionItemUrl(bookId, sessionId) {
    return bookUrl(editUrl, bookId).replace(/\/0\/$/, '/' + encodeURIComponent(sessionId) + '/');
  }

  // Resolve com o JSON da resposta; rejeita com Error (message em português)
  // para rede, sessão expirada, resposta inválida ou {success:false}.
  function api(method, url, body) {
    var headers = { 'Accept': 'application/json' };
    var opts = { method: method, credentials: 'same-origin', headers: headers };
    if (method !== 'GET') {
      headers['X-CSRFToken'] = csrf;
      if (body) {
        headers['Content-Type'] = 'application/json';
        opts.body = JSON.stringify(body);
      }
    }

    return fetch(url, opts)
      .then(function (res) {
        return res.json().then(
          function (data) { return { res: res, data: data }; },
          function () { return { res: res, data: null }; }
        );
      }, function () {
        throw apiError(MSG_NETWORK, { network: true });
      })
      .then(function (r) {
        var res = r.res, data = r.data;
        // login redirecionado (HTML) ou CSRF/permissão recusados
        if (res.redirected || res.status === 401 || (res.status === 403 && data === null)) {
          throw apiError(MSG_AUTH, { status: res.status });
        }
        if (!res.ok || (data && data.success === false)) {
          throw apiError(
            (data && data.error) || 'O servidor respondeu com erro (HTTP ' + res.status + '). Nada foi salvo.',
            { status: res.status, field: data && data.field }
          );
        }
        if (data === null) throw apiError(MSG_UNCONFIRMED, { status: res.status });
        return data;
      });
  }

  function applyState(data) {
    sessions = Array.isArray(data.sessions) ? data.sessions : [];
    bookStatus = data.book_status || null;
  }

  // Busca histórico + status do livro no servidor e atualiza o estado
  function fetchSessions(bookId) {
    return api('GET', bookUrl(sessionsUrl, bookId)).then(function (data) {
      return data;
    });
  }

  function signature(list) {
    return (list || []).map(function (s) {
      return [s.id, s.cumulative_pages, s.cumulative_percent, s.minute_count].join(':');
    }).join('|');
  }

  // Antes de gravar, confere se o histórico em tela ainda é o do servidor
  // (outra aba/dispositivo pode ter mudado). Se mudou, atualiza a tela e aborta.
  function ensureFresh(bookId) {
    return fetchSessions(bookId).then(function (data) {
      if (!current || current.id !== String(bookId)) throw apiError('Livro trocado durante a operação.');
      if (signature(data.sessions) !== signature(sessions)) {
        applyState(data);
        editingId = null;
        renderTypeUI();
        renderSummary();
        throw apiError('Seu histórico foi alterado em outra aba ou dispositivo e foi atualizado aqui. Confira os valores e tente de novo.');
      }
      return data;
    });
  }

  // ---------- Resumo (calculado só a partir das sessões vindas da API) ----------
  function summaryOf(book) {
    var last = sessions.length ? sessions[sessions.length - 1] : null;
    var percent = last ? Number(last.cumulative_percent) || 0 : 0;
    percent = Math.min(100, percent);
    if (percent > 99.999) percent = 100;

    var pagesRead = null;
    if (book.pages) {
      pagesRead = last && last.cumulative_pages != null
        ? Number(last.cumulative_pages) || 0
        : Math.round(percent * book.pages / 100);
      pagesRead = Math.min(book.pages, pagesRead);
    }

    var minutes = 0;
    sessions.forEach(function (s) { minutes += Number(s.minute_count) || 0; });

    var eta = null;
    if (minutes > 0 && percent > 0) {
      eta = Math.max(0, Math.round((100 - percent) * minutes / percent));
    } else if (book.pages) {
      eta = Math.max(0, Math.round(book.pages * (100 - percent) / 100 * MINUTES_PER_PAGE));
    }

    return { percent: percent, pagesRead: pagesRead, count: sessions.length, eta: eta };
  }

  function formatPercent(p) {
    return Math.floor(p) + '%';
  }

  // Ex.: 35,5% (até 2 casas, só para mensagens)
  function formatExactPercent(p) {
    return String(Math.round(p * 100) / 100).replace('.', ',') + '%';
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

  function parseNumber(input) {
    var v = input.value.trim().replace(',', '.');
    return v === '' ? null : Number(v);
  }

  // Devolve o que a API espera: páginas lidas na sessão (pages_read, delta) ou o
  // percentual em que parou (stopped_percent). null = inválido (erro já exibido).
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
      } else if (value <= sum.pagesRead) {
        msg = 'Você já está na página ' + sum.pagesRead + '. Informe uma página maior.';
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
    } else if (value <= sum.percent) {
      msg = 'Você já está em ' + formatExactPercent(sum.percent) + '. Informe um percentual maior.';
    }

    setError(el.amount, el.amountError, msg);
    return msg ? null : value;
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
    // o tempo é obrigatório (ReadingSession.minute_count exige >= 1)
    if (!result.msg && !result.total) result.msg = 'Informe o tempo da leitura (ex.: 1:30).';
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

  function setBusy(value) {
    busy = value;
    if (el.submit) el.submit.disabled = value;
    el.markRead.disabled = value;
  }

  // ---------- Renderização ----------
  function renderTypeUI() {
    var hasPages = !!current.pages;
    el.typePages.disabled = !hasPages;
    el.noPages.hidden = hasPages;
    // livro sem páginas: só percentual (record_type='percent')
    if (!hasPages) el.typePercent.checked = true;

    var type = currentType();
    var sum = summaryOf(current);
    var remaining = remainingFor(current, sum, type);

    if (type === 'pages') {
      el.amountLabel.textContent = 'Em qual página você parou? ';
      el.suffix.textContent = 'pág.';
      el.amount.step = '1';
      el.amount.min = '1';
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
      // só acontece em livro sem número de páginas e sem nenhuma sessão
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

  function pad2(n) { return (n < 10 ? '0' : '') + n; }

  // Ex.: "08/nov/2026 15:00"
  function formatDateTime(iso) {
    var d = new Date(iso);
    if (isNaN(d)) return '';
    return pad2(d.getDate()) + '/' + MONTHS[d.getMonth()] + '/' + d.getFullYear() +
      ' ' + pad2(d.getHours()) + ':' + pad2(d.getMinutes());
  }

  function cumPages(s) {
    return s && s.cumulative_pages != null ? Number(s.cumulative_pages) || 0 : 0;
  }

  function cumPercent(s) {
    return s ? Number(s.cumulative_percent) || 0 : 0;
  }

  function findSession(id) {
    for (var i = 0; i < sessions.length; i++) if (sessions[i].id === id) return i;
    return -1;
  }

  // Lista do pop-up (mais recente primeiro)
  function renderHistory() {
    el.historyBook.textContent = current.title;
    el.history.innerHTML = '';
    el.historyEmpty.hidden = sessions.length > 0;

    for (var i = sessions.length - 1; i >= 0; i--) {
      if (sessions[i].id === editingId) el.history.appendChild(editItem(i));
      else el.history.appendChild(historyItem(i));
    }
  }

  // Ex.: "263/433 pág. (60%)" + "08/nov/2026 15:00 · +32 págs · 1 h 30 min"
  function historyItem(i) {
    var s = sessions[i];
    var prev = i > 0 ? sessions[i - 1] : null;
    var li = document.createElement('li');
    li.className = 'rs-history-item';
    li.dataset.id = s.id;

    var text = document.createElement('div');
    text.className = 'rs-history-text';

    var title = document.createElement('strong');
    title.textContent = current.pages
      ? cumPages(s) + '/' + current.pages + ' pág. (' + formatPercent(cumPercent(s)) + ')'
      : formatPercent(cumPercent(s));

    var diff = current.pages
      ? (s.pages_read != null ? Number(s.pages_read) : cumPages(s) - cumPages(prev))
      : Math.round(cumPercent(s) - cumPercent(prev));
    var read = (diff < 0 ? '−' : '+') + Math.abs(diff) + (current.pages ? ' págs' : '%');

    var meta = document.createElement('span');
    meta.textContent = [formatDateTime(s.created_at), read, s.minute_count ? formatDuration(s.minute_count) : '']
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

  function editByPages(s) {
    return s.record_type === 'pages' && !!current.pages;
  }

  // Formulário de edição dentro do próprio item
  function editItem(i) {
    var s = sessions[i];
    var byPages = editByPages(s);

    var li = document.createElement('li');
    li.className = 'rs-history-item rs-history-item--form';
    li.dataset.id = s.id;
    li.innerHTML =
      '<form class="rs-edit" novalidate>' +
        '<div class="rs-edit-grid">' +
          '<div>' +
            '<label for="rsEditAmount">' + (byPages ? 'Página em que parou' : 'Percentual em que parou') + '</label>' +
            '<div class="rs-input-group">' +
              '<input id="rsEditAmount" name="amount" class="rs-input" type="number" inputmode="' + (byPages ? 'numeric' : 'decimal') + '" min="1" step="' + (byPages ? '1' : 'any') + '" />' +
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
    form.elements.amount.value = byPages ? cumPages(s) : cumPercent(s);
    form.elements.duration.value = s.minute_count ? formatHM(s.minute_count) : '';
    return li;
  }

  function showEditError(form, msg) {
    var box = form.querySelector('.rs-error');
    box.textContent = msg;
    box.hidden = !msg;
  }

  function setEditBusy(form, value) {
    Array.prototype.forEach.call(form.querySelectorAll('button'), function (b) { b.disabled = value; });
  }

  // Salva a edição pela API (PATCH). O servidor recalcula os acumulados de todas
  // as sessões; a tela é redesenhada com a resposta.
  function saveEdit(id, form) {
    if (busy) return;
    var idx = findSession(id);
    if (idx === -1) return;

    var s = sessions[idx];
    var prev = idx > 0 ? sessions[idx - 1] : null;
    var byPages = editByPages(s);
    var raw = form.elements.amount.value.trim().replace(',', '.');
    var value = Number(raw);
    var msg = '';

    if (raw === '' || isNaN(value) || value <= 0) {
      msg = byPages ? 'Informe a página em que parou (número inteiro).' : 'Informe o percentual como número maior que zero.';
    } else if (byPages) {
      if (!Number.isInteger(value)) msg = 'Use um número inteiro de página.';
      else if (value > current.pages) msg = 'Este livro tem ' + current.pages + ' páginas.';
      else if (value <= cumPages(prev)) msg = 'Informe uma página maior que a da atualização anterior (' + cumPages(prev) + ').';
    } else {
      if (value > 100) msg = 'O percentual vai até 100%.';
      else if (Math.round(value * 100) / 100 !== value) msg = 'Use no máximo 2 casas decimais.';
      else if (value <= cumPercent(prev)) msg = 'Informe um percentual maior que o da atualização anterior (' + formatExactPercent(cumPercent(prev)) + ').';
    }

    var dur = parseDuration(form.elements.duration.value);
    if (!msg) msg = dur.msg;
    if (!msg && !dur.total) msg = 'Informe o tempo da leitura (ex.: 1:30).';

    if (msg) { showEditError(form, msg); return; }

    // Só envia o que mudou (evita regravar um percentual arredondado sem querer)
    var body = {};
    if (value !== (byPages ? cumPages(s) : cumPercent(s))) {
      if (byPages) body.pages_read = value - cumPages(prev); // páginas lidas na sessão
      else body.stopped_percent = value;                     // posição em que parou
    }
    if (dur.total !== Number(s.minute_count)) body.minute_count = dur.total;

    if (!Object.keys(body).length) {
      editingId = null;
      renderHistory();
      return;
    }

    var bookId = current.id;
    showEditError(form, '');
    setBusy(true);
    setEditBusy(form, true);

    ensureFresh(bookId)
      .then(function () {
        return api('PATCH', sessionItemUrl(bookId, id), body);
      })
      .then(function (data) {
        if (!current || current.id !== bookId) return;
        applyState(data);
        editingId = null;
        renderTypeUI();
        renderSummary();
        notify('success', 'Atualização editada.');
      })
      .catch(function (err) {
        // erro explícito: no próprio formulário (se ainda aberto) e em toast
        var open = el.history.querySelector('.rs-edit');
        if (open) { showEditError(open, err.message); setEditBusy(open, false); }
        notify('error', err.message);
      })
      .then(function () { setBusy(false); });
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
    var type = currentType();
    var add = 0;

    // páginas: o campo é a página onde parou; %: é o percentual em que você está
    var position = type === 'pages' ? sum.pagesRead : sum.percent;
    var max = type === 'pages' ? current.pages : 100;

    if (value !== null && !isNaN(value) && value > position && value <= max) {
      var target = type === 'pages' ? value / current.pages * 100 : value;
      add = Math.max(0, target - sum.percent);
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

  function findBook(id) {
    for (var i = 0; i < books.length; i++) if (books[i].id === String(id)) return books[i];
    return null;
  }

  // ---------- Carregamento ----------
  // 1) livros "Lendo" (servidor), 2) histórico do livro escolhido (servidor).
  function load() {
    var token = ++loadToken;
    show('loading');

    api('GET', lookupUrl)
      .then(function (data) {
        if (token !== loadToken) return;

        books = (data.results || []).map(function (b) {
          return { id: String(b.id), title: b.title, author: b.author, genre: b.genre || '', pages: b.pages || null, icon: b.icon || '' };
        });

        if (!books.length) {
          current = null; sessions = []; bookStatus = null;
          show('empty');
          return;
        }

        var keep = current && findBook(current.id);
        current = keep || findBook(requestedId) || books[0];

        return fetchSessions(current.id).then(function (state) {
          if (token !== loadToken) return;
          applyState(state);
          editingId = null;
          show('content');
          renderAll();
        });
      })
      .catch(function (err) {
        if (token !== loadToken) return;
        var p = el.loadError.querySelector('p');
        if (p) p.textContent = err.message;
        show('error');
        notify('error', err.message);
      });
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
    if (busy) return;
    triedSubmit = true;

    var amount = validateAmount();
    var minutes = validateMinutes();

    if (amount === null || minutes === false) {
      (amount === null ? el.amount : el.minutes).focus();
      notify('error', 'Confira os campos destacados antes de registrar.');
      return;
    }

    var type = currentType();
    var bookId = current.id;
    var body = { record_type: type, minute_count: minutes };
    if (type === 'pages') body.pages_read = amount;
    else body.stopped_percent = amount;

    setBusy(true);

    // Confere no servidor se o livro ainda está "Lendo" e se o histórico em tela
    // é o atual; só então grava. Nada fica salvo no navegador.
    fetchSessions(bookId)
      .then(function (state) {
        if (!current || current.id !== bookId) return null;

        if (!state.book_status || state.book_status.status !== 'READING') {
          notify('error', 'Este livro não está mais marcado como “Lendo”.');
          load();
          return null;
        }
        if (signature(state.sessions) !== signature(sessions)) {
          applyState(state);
          renderTypeUI();
          renderSummary();
          notify('error', 'Seu histórico foi alterado em outra aba ou dispositivo e foi atualizado aqui. Confira os valores e registre de novo.');
          return null;
        }

        return api('POST', bookUrl(sessionUrl, bookId), body).then(function (data) {
          if (!current || current.id !== bookId) return;
          applyState(data);
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
      })
      .catch(function (err) {
        // 400 do servidor com campo conhecido: mostra junto do campo
        if (err.field === 'pages_read' || err.field === 'stopped_percent') {
          setError(el.amount, el.amountError, err.message);
        } else if (err.field === 'minute_count') {
          setError(el.minutes, el.minutesError, err.message);
        }
        notify('error', err.message);
      })
      .then(function () { setBusy(false); });
  });

  // Sugestão ao chegar em 100%
  el.markRead.addEventListener('click', function () {
    if (busy) return;
    var book = current;
    setBusy(true);

    api('POST', bookUrl(markReadUrl, book.id))
      .then(function () {
        notify('success', '“' + book.title + '” foi marcado como lido.');
        current = null; // o livro lido sai da lista; recarrega do servidor
        load();
      })
      .catch(function (err) {
        notify('error', err.message);
      })
      .then(function () { setBusy(false); });
  });

  // ---------- Pop-up do histórico ----------
  el.historyOpen.addEventListener('click', function () {
    editingId = null;
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
    editingId = null;
    closeMenus();
  });

  // Ações dos itens (menu ⋮, editar, cancelar)
  el.history.addEventListener('click', function (e) {
    var btn = e.target.closest('button');
    if (!btn || busy) return;
    var item = btn.closest('[data-id]');
    var id = item ? Number(item.dataset.id) : null;
    var action = btn.dataset.action;

    if (action === 'menu') { toggleMenu(btn); return; }
    closeMenus();

    if (action === 'edit') {
      editingId = id;
      renderHistory();
      el.history.querySelector('#rsEditAmount').focus();
    } else if (action === 'cancel') {
      editingId = null;
      renderHistory();
    }
  });

  el.history.addEventListener('submit', function (e) {
    e.preventDefault();
    var item = e.target.closest('[data-id]');
    if (item) saveEdit(Number(item.dataset.id), e.target);
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

  load();
})();
