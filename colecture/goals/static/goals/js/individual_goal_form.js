(function () {
  'use strict';

  var form = document.getElementById('individual-goal-form');
  if (!form) return;

  var $ = function (sel, root) { return (root || document).querySelector(sel); };
  var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };

  var blockPages = $('#block-pages');
  var blockTime = $('#block-time');
  var blockWeekdays = $('#block-weekdays');
  var blockDeadline = $('#block-deadline');

  var nameInput = form.elements['name'];
  var targetInput = blockPages.querySelector('input');
  var timeInput = blockTime.querySelector('input');
  var deadlineInput = blockDeadline.querySelector('input');
  var bookSelect = form.elements['book'];
  var bookPages = {};
  try { bookPages = JSON.parse(form.dataset.bookPages || '{}'); } catch (e) {}

  var PERIOD_TEXT = {
    DAILY: { label: 'por dia', hint: 'por dia' },
    WEEKDAYS: { label: 'por dia de leitura', hint: 'em cada dia escolhido' },
    WEEKLY: { label: 'por semana', hint: 'por semana' },
    MONTHLY: { label: 'por mês', hint: 'por mês' },
    TOTAL: { label: 'no total', hint: 'no total' },
  };
  var DAY_NAMES = ['seg', 'ter', 'qua', 'qui', 'sex', 'sáb', 'dom'];

  function checkedValue(name) {
    var input = form.querySelector('input[name="' + name + '"]:checked');
    return input ? input.value : '';
  }

  function setRadio(name, value) {
    var input = form.querySelector('input[name="' + name + '"][value="' + value + '"]');
    if (input) input.checked = true;
  }

  function todayISO() {
    var d = new Date();
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    return d.toISOString().slice(0, 10);
  }

  function toggle(block, active) {
    block.hidden = !active;
    $$('input, select', block).forEach(function (i) { i.disabled = !active; });
  }

  function parseMinutes(raw) {
    var m = /^(\d{1,3})(?::([0-5]\d))?$/.exec((raw || '').trim());
    if (!m) return null;
    return parseInt(m[1], 10) * 60 + parseInt(m[2] || '0', 10);
  }

  function formatMinutes(total) {
    var h = Math.floor(total / 60), m = total % 60;
    if (!h) return m + 'min';
    return m ? h + 'h' + String(m).padStart(2, '0') : h + 'h';
  }

  function update() {
    var isTime = checkedValue('goal_type') === 'HOUR_COUNT';
    var period = checkedValue('period') || 'TOTAL';
    var hasDeadline = checkedValue('duration') === 'deadline';

    toggle(blockTime, isTime);
    toggle(blockPages, !isTime);
    toggle(blockWeekdays, period === 'WEEKDAYS');
    toggle(blockDeadline, hasDeadline);

    var text = PERIOD_TEXT[period] || PERIOD_TEXT.TOTAL;
    $$('[data-target-label]', blockPages).forEach(function (el) { el.textContent = 'Páginas ' + text.label; });
    $$('[data-target-label]', blockTime).forEach(function (el) { el.textContent = 'Tempo ' + text.label; });
    $$('[data-period-hint]').forEach(function (el) { el.textContent = text.hint; });

    var maxPages = bookSelect && bookPages[bookSelect.value];
    if (maxPages) targetInput.max = String(maxPages);
    else targetInput.removeAttribute('max');

    updatePreview();
  }

  function updatePreview() {
    var emoji = checkedValue('emoji');
    var period = checkedValue('period') || 'TOTAL';
    var isTime = checkedValue('goal_type') === 'HOUR_COUNT';

    var emojiPreview = $('[data-emoji-preview]');
    var cardEmoji = $('[data-preview-emoji]');
    emojiPreview.hidden = !emoji;
    emojiPreview.textContent = emoji;
    cardEmoji.hidden = !emoji;
    cardEmoji.textContent = emoji;
    $('[data-preview-name]').textContent = nameInput.value.trim() || 'Sua meta';

    var amount = '';
    if (isTime) {
      var minutes = parseMinutes(timeInput.value);
      if (minutes) amount = formatMinutes(minutes);
    } else if (parseInt(targetInput.value, 10) > 0) {
      amount = parseInt(targetInput.value, 10) + ' páginas';
    }

    var parts = [];
    if (amount) {
      if (period === 'WEEKDAYS') {
        var days = $$('input:checked', blockWeekdays).map(function (i) { return DAY_NAMES[+i.value]; });
        parts.push(amount + (days.length ? ' · ' + days.join(', ') : ''));
      } else {
        parts.push(amount + ' ' + PERIOD_TEXT[period].label);
      }
    }
    if (bookSelect && bookSelect.value) {
      parts.push(bookSelect.options[bookSelect.selectedIndex].text);
    }
    if (checkedValue('duration') === 'deadline' && deadlineInput.value) {
      var d = deadlineInput.value.split('-');
      parts.push('até ' + d[2] + '/' + d[1]);
    }
    $('[data-preview-schedule]').textContent = parts.length ? parts.join(' · ') : 'Preencha os campos para ver a prévia';
  }

  $$('[data-preset]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var d = btn.dataset;
      nameInput.value = d.name || '';
      setRadio('emoji', d.emoji || '');
      setRadio('goal_type', d.type);
      setRadio('period', d.period);
      targetInput.value = d.target || '';
      timeInput.value = d.time || '';
      var days = (d.weekdays || '').split(',');
      $$('input', blockWeekdays).forEach(function (i) { i.checked = days.indexOf(i.value) !== -1; });

      $$('[data-preset]').forEach(function (b) { b.classList.toggle('is-active', b === btn); });
      clearClientErrors();
      update();
    });
  });

  timeInput.addEventListener('input', function () {
    var digits = timeInput.value.replace(/\D/g, '').slice(0, 5);
    timeInput.value = digits.length > 2 ? digits.slice(0, -2) + ':' + digits.slice(-2) : digits;
  });
  timeInput.addEventListener('blur', function () {
    if (timeInput.value && timeInput.value.indexOf(':') === -1) timeInput.value += ':00';
    updatePreview();
  });

  deadlineInput.min = todayISO();

  form.addEventListener('change', update);
  form.addEventListener('input', updatePreview);

  function clearClientErrors() {
    $$('.error[data-client]', form).forEach(function (el) { el.remove(); });
    $$('.field--client-error', form).forEach(function (el) {
      el.classList.remove('field--error', 'field--client-error');
    });
  }

  function addError(block, message) {
    block.classList.add('field--error', 'field--client-error');
    var span = document.createElement('span');
    span.className = 'error';
    span.dataset.client = '';
    span.textContent = message;
    block.appendChild(span);
  }

  form.addEventListener('submit', function (event) {
    clearClientErrors();
    var errors = [];

    if (!nameInput.value.trim()) {
      errors.push([nameInput.closest('.field'), 'Dê um nome para a meta.']);
    }

    if (checkedValue('goal_type') === 'HOUR_COUNT') {
      var minutes = parseMinutes(timeInput.value);
      if (minutes === null) {
        errors.push([blockTime, 'Informe o tempo no formato horas:minutos, ex.: 0:20.']);
      } else if (minutes <= 0) {
        errors.push([blockTime, 'O tempo deve ser maior que zero.']);
      }
    } else {
      var pages = Number(targetInput.value);
      if (!targetInput.value || !Number.isInteger(pages) || pages <= 0) {
        errors.push([blockPages, 'A quantidade de páginas deve ser maior que zero.']);
      } else if (targetInput.max && pages > Number(targetInput.max)) {
        errors.push([blockPages, 'A meta pode ter no máximo ' + targetInput.max + ' páginas.']);
      }
    }

    if (checkedValue('period') === 'WEEKDAYS' && !$$('input:checked', blockWeekdays).length) {
      errors.push([blockWeekdays, 'Escolha pelo menos um dia da semana.']);
    }

    if (checkedValue('duration') === 'deadline') {
      if (!deadlineInput.value) {
        errors.push([blockDeadline, 'Escolha a data limite ou marque a meta como contínua.']);
      } else if (deadlineInput.value < todayISO() && deadlineInput.value !== deadlineInput.defaultValue) {
        errors.push([blockDeadline, 'A data limite não pode estar no passado.']);
      }
    }

    if (errors.length) {
      event.preventDefault();
      errors.forEach(function (e) { addError(e[0], e[1]); });
      var first = errors[0][0].querySelector('input, select, textarea');
      if (first) first.focus();
      if (typeof showToast === 'function') {
        showToast('error', 'Não foi possível salvar a meta', errors[0][1]);
      }
    }
  });

  update();
})();
