"""Formulários do app accounts: login e cadastro.

Os formulários validam a entrada do usuário antes de ela chegar à view
(restrição arquitetural do projeto: validação com Django Forms) e entregam
à view apenas dados já limpos, em `form.cleaned_data`.
"""

from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

# Regras de tamanho da senha.
# O mínimo de 8 caracteres também é garantido pelo MinimumLengthValidator
# em settings.AUTH_PASSWORD_VALIDATORS. Repetir aqui faz o navegador exibir
# o atributo `minlength` no <input>, avisando o usuário antes do envio.
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


class LoginForm(AuthenticationForm):
    """Formulário de login (R01 / R04).

    O AuthenticationForm já exige username e senha preenchidos e confere as
    credenciais com `authenticate()` dentro do `is_valid()`. Depois disso,
    a view obtém o usuário autenticado com `form.get_user()`.

    Não há regra de tamanho de senha aqui de propósito: no login só
    interessa saber se a senha confere, quem valida a força é o cadastro.
    """

    # Mantém as mensagens originais do Django e troca só a de login inválido.
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": (
            "Nome de usuário ou senha incorretos. "
            "Lembre-se de que letras maiúsculas e minúsculas fazem diferença."
        ),
    }


class RegistrationForm(UserCreationForm):
    """Formulário de cadastro (R01 / R04).

    Campos: username, e-mail, senha e confirmação de senha.
    O `UserCreationForm` já confere se as duas senhas são iguais, se o
    username é único e aplica os validadores de senha do settings.py.
    O e-mail foi adicionado porque o User do projeto tem e-mail
    (diagrama UML do Documento de Arquitetura), e o form padrão do Django
    só pede username e senha.
    """

    email = forms.EmailField(
        label="E-mail",
        required=True,
        max_length=254,
        error_messages={
            "required": "Informe seu e-mail.",
            "invalid": "Informe um e-mail válido.",
        },
    )

    password1 = forms.CharField(
        label="Senha",
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
        strip=False,  # espaços fazem parte da senha, não devem ser removidos
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text=password_validation.password_validators_help_text_html(),
        error_messages={"required": "Informe uma senha."},
    )

    password2 = forms.CharField(
        label="Confirmação de senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Digite a mesma senha novamente, para verificação.",
        error_messages={"required": "Confirme sua senha."},
    )

    # Ordem em que os campos aparecem no formulário (ex.: com {{ form.as_p }}).
    field_order = ["username", "email", "password1", "password2"]

    class Meta(UserCreationForm.Meta):
        # Campos do model User que o form preenche e salva em form.save().
        fields = ("username", "email")

    def clean_email(self):
        """Padroniza o e-mail em minúsculas e impede e-mails repetidos.

        O model User do Django não exige e-mail único, então a checagem
        é feita aqui. Se o grupo preferir permitir e-mails repetidos,
        basta remover este método.
        """
        email = self.cleaned_data["email"].strip().lower()

        if get_user_model().objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Já existe uma conta cadastrada com este e-mail.",
                code="email_taken",
            )

        return email