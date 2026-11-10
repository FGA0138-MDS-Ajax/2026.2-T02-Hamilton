(function () {
  'use strict';

  var SESSIONS_KEY = 'colectureSessions';

  function formatAmount(goalType, amount) {
    if (goalType === 'HOUR_COUNT') {
      var h = Math.floor(amount / 60), m = amount % 60;
      if (!h) return m + 'min';
      return m ? h + 'h' + String(m).padStart(2, '0') : h + 'h';
    }
    return String(amount);
  }

  function localDateISO(isoString) {
    var d = new Date(isoString);
    if (isNaN(d)) return '';
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    return d.toISOString().slice(0, 10);
  }

  function bookPagesFor(bookId, fallback) {
    var shelfCard = document.querySelector('[data-shelf-book][data-book-id="' + bookId + '"]');
    var pages = shelfCard && Number(shelfCard.getAttribute('data-pages'));
    return pages || Number(fallback) || 0;
  }

  var card = document.querySelector('[data-goal-card]');
  if (card) {
    var d = card.dataset;
    var goalType = d.goalType;
    var target = Number(d.goalTarget) || 0;
    var serverCurrent = Number(d.goalServerCurrent) || 0;
    var start = d.goalStart || '';
    var end = d.goalEnd || '';
    var goalBookId = d.goalBookId || '';
    var periodLabel = d.goalPeriodLabel || '';
    var restDay = d.goalRestDay === 'true';

    var localCurrent = 0;
    try {
      var allSessions = JSON.parse(localStorage.getItem(SESSIONS_KEY) || '{}') || {};
      Object.keys(allSessions).forEach(function (bookId) {
        if (goalBookId && String(bookId) !== String(goalBookId)) return;
        var pages = bookPagesFor(bookId, d.goalBookPages);
        var list = Array.isArray(allSessions[bookId]) ? allSessions[bookId] : [];
        list.forEach(function (s) {
          var day = localDateISO(s.date);
          if (!day || (start && day < start) || (end && day > end)) return;
          if (goalType === 'HOUR_COUNT') {
            localCurrent += Math.max(0, Number(s.minutes) || 0);
          } else if (s.type === 'pages') {
            localCurrent += Math.max(0, Math.round(Number(s.amount) || 0));
          } else if (s.type === 'percent' && pages > 0) {
            localCurrent += Math.max(0, Math.round((Number(s.percent) || 0) * pages / 100));
          }
        });
      });
    } catch (e) {}

    if (localCurrent > 0 && target > 0) {
      var current = serverCurrent + localCurrent;
      var percent = Math.min(100, Math.round(current / target * 100));
      var done = current >= target;
      var remaining = Math.max(0, target - current);

      var ring = card.querySelector('[data-goal-ring]');
      var ringVal = card.querySelector('[data-goal-ring-value]');
      var countEl = card.querySelector('[data-goal-count]');
      var statusEl = card.querySelector('[data-goal-status]');

      if (ring) {
        ring.style.setProperty('--p', percent);
        ring.setAttribute('aria-valuenow', String(percent));
        ring.classList.toggle('goal-ring--done', done);
      }
      if (ringVal) {
        ringVal.innerHTML = done ? '<i class="bx bx-check" aria-hidden="true"></i>' : percent + '%';
      }
      if (countEl) {
        countEl.textContent = formatAmount(goalType, current) + '/' + formatAmount(goalType, target);
      }
      if (statusEl) {
        if (done) {
          statusEl.textContent = 'Meta batida ' + periodLabel + '! 🎉';
        } else if (!restDay) {
          var unit = goalType === 'PAGE_COUNT' ? ' páginas.' : '.';
          statusEl.textContent = 'Faltam ' + formatAmount(goalType, remaining) + unit;
        }
      }
    }
  }

  var modal = document.querySelector('[data-goal-delete-modal]');
  var openBtn = document.querySelector('[data-goal-delete-open]');
  if (!modal || !openBtn) return;

  function open() {
    modal.hidden = false;
    modal.querySelector('.modal-cancel').focus();
  }

  function close() {
    modal.hidden = true;
    openBtn.focus();
  }

  openBtn.addEventListener('click', open);
  modal.querySelectorAll('[data-goal-delete-close]').forEach(function (b) {
    b.addEventListener('click', close);
  });
  modal.addEventListener('click', function (e) {
    if (e.target === modal) close();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !modal.hidden) close();
  });
  modal.querySelector('form').addEventListener('submit', function () {
    modal.querySelectorAll('button').forEach(function (b) { b.disabled = true; });
  });
})();
