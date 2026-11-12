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
