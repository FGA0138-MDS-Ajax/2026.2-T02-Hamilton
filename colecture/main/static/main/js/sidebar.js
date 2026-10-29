(function () {
  var body = document.body;
  var toggle = document.getElementById('menuToggle');
  var overlay = document.getElementById('overlay');
  var KEY = 'colecture-sidebar-closed';
  var mobile = window.matchMedia('(max-width: 768px)');

  function setClosed(closed, save) {
    body.classList.toggle('sidebar-closed', closed);
    toggle.setAttribute('aria-expanded', String(!closed));
    toggle.setAttribute('aria-label', closed ? 'Abrir menu' : 'Fechar menu');
    if (save && !mobile.matches) { try { localStorage.setItem(KEY, closed ? '1' : '0'); } catch (e) {} }
  }

  // Estado inicial: celular começa fechada; no desktop lembra a última escolha
  var saved = null;
  try { saved = localStorage.getItem(KEY); } catch (e) {}
  setClosed(mobile.matches ? true : saved === '1', false);

  toggle.addEventListener('click', function () { setClosed(!body.classList.contains('sidebar-closed'), true); });
  overlay.addEventListener('click', function () { setClosed(true, false); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && mobile.matches) setClosed(true, false); });

  // Ao redimensionar entre celular e desktop, reajusta
  mobile.addEventListener('change', function (e) {
    var s = null; try { s = localStorage.getItem(KEY); } catch (err) {}
    setClosed(e.matches ? true : s === '1', false);
  });
})();
