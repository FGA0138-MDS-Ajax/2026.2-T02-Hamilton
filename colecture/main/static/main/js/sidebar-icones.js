(function () {
  var body = document.body;
  var toggle = document.getElementById('railToggle');
  var KEY = 'colecture-rail-collapsed';

  function setCollapsed(c) {
    body.classList.toggle('rail-collapsed', c);
    toggle.setAttribute('aria-expanded', String(!c));
    toggle.setAttribute('aria-label', c ? 'Expandir menu' : 'Recolher menu');
    try { localStorage.setItem(KEY, c ? '1' : '0'); } catch (e) {}
  }

  var saved = null;
  try { saved = localStorage.getItem(KEY); } catch (e) {}
  setCollapsed(saved === '1');

  toggle.addEventListener('click', function () { setCollapsed(!body.classList.contains('rail-collapsed')); });
})();
