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
