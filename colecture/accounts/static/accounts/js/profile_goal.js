(function () {
  'use strict';

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

(function () {
  'use strict';

  var modal = document.querySelector('[data-notifications-modal]');
  var openBtn = document.querySelector('[data-notifications-open]');
  if (!modal || !openBtn) return;

  var closeBtn = modal.querySelector('[data-notifications-close]');
  var badge = openBtn.querySelector('[data-notifications-badge]');
  var list = modal.querySelector('[data-notifications-list]');
  var emptyState = modal.querySelector('[data-notifications-empty]');
  var markReadUrl = modal.getAttribute('data-notifications-read-url');
  var csrf = modal.getAttribute('data-csrf');
  var markedRead = !badge;

  function postAction(url) {
    return fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      keepalive: true,
      headers: {
        'X-CSRFToken': csrf,
        'X-Requested-With': 'XMLHttpRequest',
      },
    });
  }

  function open() {
    modal.hidden = false;
    openBtn.setAttribute('aria-expanded', 'true');
    if (badge) badge.hidden = true;
    if (!markedRead && markReadUrl) {
      markedRead = true;
      postAction(markReadUrl).catch(function () {
        markedRead = false;
      });
    }
    if (closeBtn) closeBtn.focus();
  }

  function close() {
    modal.hidden = true;
    openBtn.setAttribute('aria-expanded', 'false');
    openBtn.focus();
  }

  openBtn.addEventListener('click', open);
  modal.querySelectorAll('[data-notifications-close]').forEach(function (b) {
    b.addEventListener('click', close);
  });
  modal.addEventListener('click', function (e) {
    if (e.target === modal) {
      close();
      return;
    }

    var hideBtn = e.target.closest('[data-notification-hide]');
    if (!hideBtn || hideBtn.disabled) return;

    var item = hideBtn.closest('[data-notification-item]');
    var hideUrl = hideBtn.getAttribute('data-notification-hide');
    if (!item || !hideUrl) return;

    hideBtn.disabled = true;
    postAction(hideUrl)
      .then(function (res) {
        if (!res.ok) throw new Error();
        item.remove();
        if (list && list.querySelectorAll('[data-notification-item]').length === 0) {
          list.hidden = true;
          if (emptyState) emptyState.hidden = false;
        }
      })
      .catch(function () {
        hideBtn.disabled = false;
      });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !modal.hidden) close();
  });
})();
