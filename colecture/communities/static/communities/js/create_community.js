/* Página de criação de comunidade: pesquisa de livro e validação dos campos obrigatórios. */
(function () {
  'use strict';

  var MAX_RESULTS = 5;
  var ICON_ERROR = '<svg class="icon" aria-hidden="true"><use href="#i-error"></use></svg> ';

  var form = document.getElementById('community-form');
  if (!form) return;

  function norm(text) {
    return (text || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }

  /* ---------- Placeholders ---------- */
  var nameInput = form.querySelector('[name="name"]');
  var descInput = form.querySelector('[name="description"]');
  if (nameInput && !nameInput.placeholder) nameInput.placeholder = 'Ex.: Clube do Machado';
  if (descInput) {
    if (!descInput.placeholder) descInput.placeholder = 'Sobre o que é a comunidade e o que vocês vão ler?';
    descInput.rows = 6;
  }

  /* ---------- Erros (mesmo estilo dos erros do servidor) ---------- */
  function clearError(field) {
    field.classList.remove('field--invalid');
    Array.prototype.forEach.call(field.querySelectorAll('.field-error'), function (p) { p.remove(); });
  }

  function showError(field, text) {
    clearError(field);
    field.classList.add('field--invalid');
    var p = document.createElement('p');
    p.className = 'field-error';
    p.setAttribute('role', 'alert');
    p.innerHTML = ICON_ERROR;
    p.appendChild(document.createTextNode(text));
    field.appendChild(p);
  }

  /* ---------- Pesquisa de livro (mesma busca da pagina /search) ---------- */
  var hidden = document.getElementById('id_book');
  var titleField = document.getElementById('book-title');
  var authorField = document.getElementById('book-author');
  var search = document.getElementById('book-search');
  var searchBox = document.getElementById('book-search-box');
  var list = document.getElementById('book-results');
  var chip = document.getElementById('book-selected');
  var chipTitle = document.getElementById('book-selected-title');
  var chipAuthor = document.getElementById('book-selected-author');
  var changeBtn = document.getElementById('book-change');
  var picker = document.getElementById('book-picker');
  var searchUrl = picker.getAttribute('data-search-url');

  var shown = [];
  var active = -1;
  var timer = null;
  var requestId = 0;

  function openList() {
    list.hidden = false;
    search.setAttribute('aria-expanded', 'true');
  }

  function closeList() {
    list.hidden = true;
    search.setAttribute('aria-expanded', 'false');
    active = -1;
  }

  function addNote(text) {
    var li = document.createElement('li');
    li.className = 'book-note';
    li.setAttribute('role', 'presentation');
    li.textContent = text;
    list.appendChild(li);
  }

  function showNote(text) {
    list.innerHTML = '';
    shown = [];
    addNote(text);
    openList();
  }

  function setActive(index) {
    var items = list.querySelectorAll('.book-result');
    Array.prototype.forEach.call(items, function (el, i) { el.classList.toggle('is-active', i === index); });
    active = index;
  }

  function renderResults(results, total) {
    shown = results.slice(0, MAX_RESULTS);
    list.innerHTML = '';
    active = -1;

    if (!shown.length) {
      addNote('Nenhum livro encontrado. Tente outro título ou autor.');
    } else {
      shown.forEach(function (b, i) {
        var li = document.createElement('li');
        li.className = 'book-result';
        li.setAttribute('role', 'option');
        li.setAttribute('data-index', i);
        var t = document.createElement('span');
        t.className = 'book-result-title';
        t.textContent = b.title;
        li.appendChild(t);
        if (b.author) {
          var a = document.createElement('span');
          a.className = 'book-result-author';
          a.textContent = b.author;
          li.appendChild(a);
        }
        list.appendChild(li);
      });
      if (total > shown.length) {
        addNote('Mostrando ' + shown.length + ' de ' + total + '. Digite para refinar a busca.');
      }
    }
    openList();
  }

  function fetchBooks() {
    var current = ++requestId;
    showNote('Buscando livros…');
    fetch(searchUrl + '?q=' + encodeURIComponent(search.value.trim()), { headers: { 'Accept': 'application/json' } })
      .then(function (res) {
        if (!res.ok) throw new Error('Falha na busca');
        return res.json();
      })
      .then(function (data) {
        if (current !== requestId) return; // ignora respostas antigas
        renderResults(data.results || [], data.total || 0);
      })
      .catch(function () {
        if (current !== requestId) return;
        showNote('Não foi possível buscar os livros. Tente novamente.');
      });
  }

  function scheduleFetch() {
    clearTimeout(timer);
    timer = setTimeout(fetchBooks, 250);
  }

  function select(book) {
    hidden.value = book.id;
    titleField.value = book.title;
    authorField.value = book.author || '';
    chipTitle.textContent = book.title;
    chipAuthor.textContent = book.author || '';
    chip.hidden = false;
    searchBox.hidden = true;
    closeList();
    clearError(hidden.closest('.field'));
  }

  function clearSelection() {
    hidden.value = '';
    titleField.value = '';
    authorField.value = '';
    chip.hidden = true;
    searchBox.hidden = false;
    search.value = '';
    search.focus();
  }

  search.addEventListener('focus', fetchBooks);
  search.addEventListener('input', scheduleFetch);

  search.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (shown.length) setActive((active + 1) % shown.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (shown.length) setActive((active - 1 + shown.length) % shown.length);
    } else if (e.key === 'Enter') {
      if (!list.hidden && shown[active]) { e.preventDefault(); select(shown[active]); }
      else if (!list.hidden && shown.length === 1) { e.preventDefault(); select(shown[0]); }
    } else if (e.key === 'Escape') {
      closeList();
    }
  });

  list.addEventListener('click', function (e) {
    var item = e.target.closest('.book-result');
    if (item) select(shown[Number(item.getAttribute('data-index'))]);
  });

  changeBtn.addEventListener('click', clearSelection);

  document.addEventListener('click', function (e) {
    if (!picker.contains(e.target)) closeList();
  });

  // Livro já escolhido (ex.: formulário reexibido após erro de validação)
  if (hidden.value && titleField.value) {
    select({ id: hidden.value, title: titleField.value, author: authorField.value });
  } else {
    hidden.value = '';
  }

  /* ---------- Validacao dos campos obrigatorios ---------- */

  var messagesByField = {
    name: 'Informe o nome da comunidade.',
    book: 'Selecione o livro da comunidade.',
    description: 'Escreva uma descrição para a comunidade.'
  };

  form.addEventListener('submit', function (e) {
    var firstInvalid = null;
    Array.prototype.forEach.call(form.querySelectorAll('[data-required]'), function (field) {
      var key = field.getAttribute('data-required');
      var input = field.querySelector('[name="' + key + '"]');
      if (!input) return;
      if (!input.value.trim()) {
        showError(field, messagesByField[key]);
        if (!firstInvalid) firstInvalid = (key === 'book') ? search : input;
      } else {
        clearError(field);
      }
    });
    if (firstInvalid) {
      e.preventDefault();
      firstInvalid.focus();
    }
  });

  form.addEventListener('input', function (e) {
    var field = e.target.closest('[data-required]');
    if (field && e.target.name !== undefined && e.target.value && e.target.value.trim() && e.target.id !== 'book-search') {
      clearError(field);
    }
  });
})();