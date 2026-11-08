/* Página de gerenciar: confirmação antes de banir, promover ou rebaixar. */

(function () {
  function each(selector, fn) {
    Array.prototype.forEach.call(document.querySelectorAll(selector), fn);
  }

  // fecha qualquer diálogo pelo botão "Cancelar"
  each('.mod-dialog [data-close]', function (btn) {
    btn.addEventListener('click', function () { btn.closest('dialog').close(); });
  });

  // banir
  var banDialog = document.getElementById('ban-dialog');
  if (banDialog) {
    var banForm = document.getElementById('ban-form');
    var banName = document.getElementById('ban-name');

    each('[data-ban]', function (btn) {
      btn.addEventListener('click', function () {
        banForm.setAttribute('action', btn.getAttribute('data-action'));
        banName.textContent = btn.getAttribute('data-name');
        banDialog.showModal();
      });
    });
  }

  // promover / rebaixar
  var roleDialog = document.getElementById('role-dialog');
  if (roleDialog) {
    var roleForm = document.getElementById('role-form');
    var roleValue = document.getElementById('role-value');
    var roleTitle = document.getElementById('role-title');
    var roleName = document.getElementById('role-name');
    var roleText = document.getElementById('role-text');
    var roleSubmit = document.getElementById('role-submit');

    var copy = {
      MODERATOR: {
        title: 'Promover a moderador?',
        text: 'poderá aceitar solicitações, gerenciar membros e metas da comunidade.',
        button: 'Promover'
      },
      MEMBER: {
        title: 'Rebaixar a membro?',
        text: 'deixa de ser moderador e perde as permissões de gerenciamento.',
        button: 'Rebaixar'
      }
    };

    each('[data-role]', function (btn) {
      btn.addEventListener('click', function () {
        var value = btn.getAttribute('data-role-value');
        var c = copy[value];
        roleForm.setAttribute('action', btn.getAttribute('data-action'));
        roleValue.value = value;
        roleTitle.textContent = c.title;
        roleName.textContent = btn.getAttribute('data-name');
        roleText.textContent = c.text;
        roleSubmit.textContent = c.button;
        roleDialog.showModal();
      });
    });
  }
})();
