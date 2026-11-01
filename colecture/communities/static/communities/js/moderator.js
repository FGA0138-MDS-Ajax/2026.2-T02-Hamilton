/* Página de gerenciar: confirmação antes de banir. */

(function () {
  var dialog = document.getElementById('ban-dialog');
  if (!dialog) return;

  var form = document.getElementById('ban-form');
  var name = document.getElementById('ban-name');

  Array.prototype.forEach.call(document.querySelectorAll('[data-ban]'), function (btn) {
    btn.addEventListener('click', function () {
      form.setAttribute('action', btn.getAttribute('data-action'));
      name.textContent = btn.getAttribute('data-name');
      dialog.showModal();
    });
  });

  dialog.querySelector('[data-close]').addEventListener('click', function () { dialog.close(); });
})();