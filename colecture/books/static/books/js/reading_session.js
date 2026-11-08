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
    picker: $('[data-rs-picker]'),
    select: $('#rsBook'),
    cover: $('[data-rs-cover]'),
    coverEmpty: $('[data-rs-cover-empty]'),
    title: $('[data-rs-title]'),
    author: $('[data-rs-author]'),
    genre: $('[data-rs-genre]'),
    pagesTotal: $('[data-rs-pages-total]'),
    history: $('[data-rs-history]'),
    historyEmpty: $('[data-rs-history-empty]'),
    clear: $('[data-rs-clear]'),
    percent: $('[data-rs-percent]'),
    bar: $('[data-rs-bar]'),
    fill: $('[data-rs-fill]'),
    preview: $('[data-rs-preview]'),
    detail: $('[data-rs-detail]'),
    eta: $('[data-rs-eta]'),
    count: $('[data-rs-count]'),
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
    localStorage.setItem(key, JSON.stringify(data)); // pode lançar erro (cota/privado)
  }

  function readingIds() {
    var shelf = readStore(SHELF_KEY);
    return Object.keys(shelf).filter(function (id) { return shelf[id] === 'READING'; });
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

  // ---------- Cálculos ----------

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

    // Tempo para terminar:
    //  - se alguma sessão tem tempo informado, usa a média real do usuário (minutos por 1%);
    //  - senão, estima pelas páginas que faltam × velocidade média (MINUTES_PER_PAGE);
    //  - livro sem páginas e sem tempo informado: não dá para estimar (null).
    var eta = null;
    if (minutes > 0 && timedPercent > 0) {
      eta = Math.max(0, Math.round((100 - percent) * minutes / timedPercent));
    } else if (book.pages) {
      eta = Math.max(0, Math.round(book.pages * (100 - percent) / 100 * MINUTES_PER_PAGE));
    }

    return { percent: percent, pagesRead: pagesRead, count: list.length, eta: eta };
  }

  function formatPercent(p) {
    // sempre inteiro; arredonda para baixo para não mostrar 100% antes de terminar
    return Math.floor(p) + '%';
  }

  function formatMinutes(total) {
    if (total < 1) return 'menos de 1 min';
    var h = Math.floor(total / 60);
    var m = total % 60;
    if (!h) return '~' + m + ' min';
    return '~' + h + ' h' + (m ? ' ' + m + ' min' : '');
  }

  function currentType() {
    return el.typePercent.checked ? 'percent' : 'pages';
  }

  // Limpa os campos mantendo o tipo de registro escolhido
  function resetForm() {
    var type = currentType();
    el.form.reset();
    (type === 'percent' ? el.typePercent : el.typePages).checked = true;
    triedSubmit = false;
    clearErrors();
  }

  function remainingFor(book, sum, type) {
    if (type === 'pages') return book.pages - sum.pagesRead;
    // inteiro e coerente com o progresso exibido (37% lido -> restam 63%)
    return 100 - Math.floor(sum.percent);
  }

  // Quanto (em %) a quantidade digitada soma ao livro
  function sessionPercent(book, sum, type, amount) {
    if (type === 'pages') {
      // Calcula pelo total de páginas depois da sessão para fechar 100% sem erro de arredondamento
      return ((sum.pagesRead + amount) / book.pages) * 100 - sum.percent;
    }
    return amount;
  }

  // ---------- Validação (F04) ----------
  function parseNumber(input) {
    var v = input.value.trim().replace(',', '.');
    return v === '' ? null : Number(v);
  }

  // Por páginas, o usuário informa EM QUAL PÁGINA PAROU; aqui isso vira
  // quantas páginas leu na sessão (página atual - páginas já lidas).
  // Retorna a quantidade lida (páginas ou %) ou null se inválido.
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
      } else if (value <= sum.pagesRead) {
        msg = 'Você já está na página ' + sum.pagesRead + '. Informe uma página maior.';
      } else if (value > current.pages) {
        msg = 'Este livro tem ' + current.pages + ' páginas.';
      }
      setError(el.amount, el.amountError, msg);
      return msg ? null : value - sum.pagesRead;
    }

    var remaining = remainingFor(current, sum, type);
    if (value === null || isNaN(value)) {
      msg = 'Informe o percentual lido hoje.';
    } else if (value <= 0) {
      msg = 'A quantidade precisa ser maior que zero.';
    } else if (!Number.isInteger(value)) {
      msg = 'Use um número inteiro de percentual (ex.: 12).';
    } else if (value > remaining) {
      msg = 'Faltam só ' + formatPercent(remaining) + ' para terminar o livro.';
    }

    setError(el.amount, el.amountError, msg);
    return msg ? null : value;
  }

  // Máscara "h:mm": o usuário digita só números e os dois últimos viram os minutos.
  // Ex.: "45" -> 45 (min) | "130" -> "1:30" | "1230" -> "12:30".
  // (o teclado numérico do celular não tem ":", por isso a máscara)
  function maskDuration(value) {
    var d = value.replace(/\D/g, '').replace(/^0+(?=\d{3})/, '').slice(0, 4);
    return d.length > 2 ? d.slice(0, -2) + ':' + d.slice(-2) : d;
  }

  // Tempo da sessão em "h:mm" (ou só minutos, ex.: "45").
  // Retorna o total em minutos (0 se vazio) ou false se inválido.
  function validateMinutes() {
    var raw = el.minutes.value.trim();
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

    setError(el.minutes, el.minutesError, msg);
    return msg ? false : total;
  }

  // Ex.: 90 -> "1 h 30 min"
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
      el.amountLabel.textContent = 'Em qual página você parou?';
      el.suffix.textContent = 'pág.';
      el.amount.step = '1';
      el.amount.min = String(sum.pagesRead + 1);
      el.amount.max = String(current.pages);
      el.amount.setAttribute('inputmode', 'numeric');
      el.remaining.textContent = sum.pagesRead
        ? 'Você está na página ' + sum.pagesRead + ' de ' + current.pages + '. Restam ' + remaining + ' páginas.'
        : 'Você ainda não registrou nenhuma página (total: ' + current.pages + ').';
    } else {
      el.amountLabel.textContent = 'Percentual lido';
      el.suffix.textContent = '%';
      el.amount.step = '1';
      el.amount.min = '1';
      el.amount.max = String(remaining);
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

    el.count.textContent = String(sum.count);

    el.finished.hidden = !done;
    el.fields.disabled = done;

    renderPreview();
    renderHistory();
  }

  // Lista das sessões do livro selecionado (mais recente primeiro)
  function renderHistory() {
    var list = sessionsOf(current.id).slice().reverse();
    el.history.innerHTML = '';
    el.historyEmpty.hidden = list.length > 0;

    list.forEach(function (s) {
      var li = document.createElement('li');
      li.className = 'rs-history-item';

      var icon = document.createElement('span');
      icon.className = 'rs-history-icon';
      icon.innerHTML = '<i class="bx ' + (s.type === 'pages' ? 'bx-book-open' : 'bx-pie-chart-alt') + '" aria-hidden="true"></i>';

      var text = document.createElement('div');
      text.className = 'rs-history-text';
      var title = document.createElement('strong');
      title.textContent = s.type !== 'pages'
        ? 'Registrou ' + s.amount + '%'
        : (s.page
            ? 'Parou na página ' + s.page
            : 'Registrou ' + s.amount + (s.amount === 1 ? ' página' : ' páginas')); // sessões antigas
      var meta = document.createElement('span');
      var date = new Date(s.date);
      meta.textContent = (isNaN(date) ? '' : date.toLocaleDateString('pt-BR')) +
        (s.minutes ? ' · ' + formatDuration(s.minutes) : '');
      text.appendChild(title);
      text.appendChild(meta);

      var pill = document.createElement('span');
      pill.className = 'rs-history-pill';
      // Mostra as páginas lidas na sessão; registro por % é convertido pelo total do livro
      var pagesInSession = s.type === 'pages'
        ? s.amount
        : (current.pages ? Math.round((Number(s.percent) || 0) * current.pages / 100) : null);
      pill.textContent = pagesInSession !== null
        ? '+' + pagesInSession + ' págs'
        : '+' + Math.round(Number(s.percent) || 0) + '%'; // livro sem nº de páginas


      li.appendChild(icon);
      li.appendChild(text);
      li.appendChild(pill);
      el.history.appendChild(li);
    });
  }

  // Faixa listrada mostrando o que a sessão digitada vai somar
  function renderPreview() {
    var sum = summaryOf(current);
    var value = parseNumber(el.amount);
    var add = 0;
    var type = currentType();

    // por páginas o campo é a página onde parou -> converte para páginas lidas
    if (type === 'pages' && value !== null) value = value - sum.pagesRead;

    if (value !== null && !isNaN(value) && value > 0 && value <= remainingFor(current, sum, type)) {
      add = Math.max(0, sessionPercent(current, sum, type, value));
    }

    el.preview.style.left = sum.percent + '%';
    el.preview.style.width = Math.min(add, 100 - sum.percent) + '%';
  }

  function renderPicker() {
    el.select.innerHTML = '';
    books.forEach(function (b) {
      var opt = document.createElement('option');
      opt.value = b.id;
      opt.textContent = b.title;
      el.select.appendChild(opt);
    });
    el.select.value = current.id;
    el.picker.hidden = books.length < 2; // com um livro só, o seletor não precisa aparecer
  }

  function renderAll() {
    renderPicker();
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
        current = keep ? findBook(current.id) : books[0];
        show('content');
        renderAll();
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
  el.select.addEventListener('change', function () {
    current = findBook(el.select.value);
    resetForm();
    renderTypeUI();
    renderSummary();
  });

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
    try {
      var shelf = readStore(SHELF_KEY);
      shelf[current.id] = 'READ';
      writeStore(SHELF_KEY, shelf);
    } catch (err) {
      notify('error', 'Não foi possível marcar o livro como lido. Tente de novo.');
      return;
    }

    notify('success', '“' + current.title + '” foi marcado como lido.');
    books = books.filter(function (b) { return b.id !== current.id; });

    if (!books.length) { show('empty'); return; }
    current = books[0];
    renderAll();
  });

  el.retry.addEventListener('click', load);

  // Se o status mudar em outra aba do navegador, recarrega
  window.addEventListener('storage', function (e) {
    if (e.key === SHELF_KEY) load();
    if (e.key === SESSIONS_KEY && current) { renderTypeUI(); renderSummary(); }
  });

  load();
})();