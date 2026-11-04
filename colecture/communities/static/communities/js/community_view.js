/* Página da comunidade: menu de três pontinhos e confirmações (sair / arquivar). */
(function () {
  var menu = document.querySelector('[data-menu]');

  if (menu) {
    var button = menu.querySelector('.menu-btn');
    var list = menu.querySelector('.menu-list');

    function items() {
      return Array.prototype.slice.call(list.querySelectorAll('[role="menuitem"]'));
    }

    function setOpen(open, focusFirst) {
      list.hidden = !open;
      button.setAttribute('aria-expanded', String(open));
      if (open && focusFirst && items().length) items()[0].focus();
    }

    button.addEventListener('click', function () {
      setOpen(list.hidden, false);
    });

    button.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); setOpen(true, true); }
    });

    list.addEventListener('keydown', function (e) {
      var all = items();
      var i = all.indexOf(document.activeElement);
      if (e.key === 'ArrowDown') { e.preventDefault(); all[(i + 1) % all.length].focus(); }
      if (e.key === 'ArrowUp') { e.preventDefault(); all[(i - 1 + all.length) % all.length].focus(); }
      if (e.key === 'Home') { e.preventDefault(); all[0].focus(); }
      if (e.key === 'End') { e.preventDefault(); all[all.length - 1].focus(); }
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !list.hidden) { setOpen(false); button.focus(); }
    });

    // Clicar fora fecha o menu
    document.addEventListener('click', function (e) {
      if (!list.hidden && !menu.contains(e.target)) setOpen(false);
    });

    // Tab para fora do menu também fecha
    menu.addEventListener('focusout', function (e) {
      if (e.relatedTarget && !menu.contains(e.relatedTarget)) setOpen(false);
    });

    // Opções que pedem confirmação abrem o <dialog> correspondente
    Array.prototype.forEach.call(list.querySelectorAll('[data-confirm]'), function (item) {
      item.addEventListener('click', function () {
        var dialog = document.getElementById('confirm-' + item.getAttribute('data-confirm'));
        setOpen(false);
        if (dialog) dialog.showModal();
      });
    });
  }

  Array.prototype.forEach.call(document.querySelectorAll('dialog [data-close]'), function (btn) {
    btn.addEventListener('click', function () { btn.closest('dialog').close(); });
  });
})();

(function () {
  var goals = document.querySelector('.goals');
  if (!goals) return;

  function toast(type, title, desc) {
    if (typeof showToast === 'function') showToast(type, title, desc || '');
  }

  Array.prototype.forEach.call(document.querySelectorAll('[data-flash]'), function (el) {
    toast(el.getAttribute('data-type'), el.textContent.trim());
  });

  var tabs = Array.prototype.slice.call(goals.querySelectorAll('[role="tab"]'));

  function selectTab(tab, focus) {
    tabs.forEach(function (t) {
      var on = t === tab;
      t.classList.toggle('is-selected', on);
      t.setAttribute('aria-selected', String(on));
      t.tabIndex = on ? 0 : -1;
      document.getElementById(t.getAttribute('aria-controls')).hidden = !on;
    });
    if (focus) tab.focus();
  }

  tabs.forEach(function (tab, i) {
    tab.addEventListener('click', function () { selectTab(tab, false); });
    tab.addEventListener('keydown', function (e) {
      var next = null;
      if (e.key === 'ArrowRight') next = tabs[(i + 1) % tabs.length];
      if (e.key === 'ArrowLeft') next = tabs[(i - 1 + tabs.length) % tabs.length];
      if (e.key === 'Home') next = tabs[0];
      if (e.key === 'End') next = tabs[tabs.length - 1];
      if (next) { e.preventDefault(); selectTab(next, true); }
    });
  });

  Array.prototype.forEach.call(goals.querySelectorAll('[data-no-forum]'), function (btn) {
    btn.addEventListener('click', function () {
      toast('error', 'Fórum indisponível', 'Esta meta ainda não tem um fórum.');
    });
  });

  var dialog = document.getElementById('confirm-conclude');
  if (dialog) {
    var form = document.getElementById('concludeForm');
    var nameEl = document.getElementById('concludeName');
    Array.prototype.forEach.call(goals.querySelectorAll('[data-conclude]'), function (btn) {
      btn.addEventListener('click', function () {
        form.action = btn.getAttribute('data-url');
        nameEl.textContent = btn.getAttribute('data-name');
        dialog.showModal();
      });
    });
  }
})();

(function () {
  var btn = document.querySelector('[data-copy]');
  if (!btn) return;
  var input = document.querySelector(btn.getAttribute('data-copy'));

  function done() {
    if (typeof showToast === 'function') showToast('success', 'Código copiado', input.value);
  }

  btn.addEventListener('click', function () {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(input.value).then(done, fallback);
    } else {
      fallback();
    }
  });

  function fallback() {
    input.focus();
    input.select();
    try {
      if (document.execCommand('copy')) done();
    } catch (e) {}
  }
})();
