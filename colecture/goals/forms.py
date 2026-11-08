import re
from datetime import datetime, time

from django import forms
from django.utils import timezone

from .models import GOAL_DESC_MAX_LENGTH, Goal, ReadingSession

# teto de páginas quando não há livro (ou o livro não tem nº de páginas)
MAX_GOAL_PAGES = 100_000


class GoalForm(forms.ModelForm):
    # só a data: o prazo vale até o fim do dia escolhido (ver clean_deadline)
    deadline = forms.DateField(
        label="Prazo",
        required=False,
        # aceita também data e hora, formato antigo do campo
        input_formats=["%Y-%m-%d", "%Y-%m-%dT%H:%M"],
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        help_text="Opcional. Sem prazo, a meta fica aberta até ser concluída.",
    )
    # meta de tempo: o usuário digita HH:MM e o clean() converte em minutos,
    # que é a unidade em que o alvo de HOUR_COUNT é guardado
    target_time = forms.CharField(
        label="Tempo de leitura",
        required=False,
        max_length=6,
        widget=forms.TextInput(attrs={
            "inputmode": "numeric",
            "placeholder": "00:00",
            "autocomplete": "off",
        }),
        help_text="Horas e minutos, ex.: 1:30",
    )

    class Meta:
        model = Goal
        # os donos NÃO estão aqui: não podem ser trocados por POST
        fields = [
            "name", "description", "goal_type", "target",
            "deadline", "book", "status",
        ]
        labels = {
            "name": "Nome da meta",
            "description": "Descrição",
            "goal_type": "Tipo de meta",
            "target": "Quantidade-alvo",
            "book": "Livro",
            "status": "Status",
        }
        help_texts = {
            "description": "Opcional. Explique o objetivo da meta.",
            "target": "Total de páginas a ler.",
            "book": "Opcional. Livro ao qual a meta se refere.",
        }
        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "Ex.: Ler 1000 páginas em novembro",
            }),
            "description": forms.Textarea(attrs={
                "rows": 4,
                "maxlength": GOAL_DESC_MAX_LENGTH,
                "placeholder": "Descreva a meta (opcional)...",
            }),
            "target": forms.NumberInput(attrs={"placeholder": "Ex.: 300", "min": 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # o alvo vem de "target" (páginas) ou de "target_time" (tempo);
        # quem é obrigatório depende do tipo, então a checagem fica no clean()
        self.fields["target"].required = False
        # na edição de meta de tempo, mostra os minutos guardados como HH:MM
        if self.instance.pk and self.instance.goal_type == Goal.GoalType.HOUR_COUNT:
            hours, minutes = divmod(self.instance.target, 60)
            self.initial["target_time"] = f"{hours}:{minutes:02d}"
            self.initial["target"] = None
        # na edição, mostra a data no fuso local (o banco guarda em UTC)
        if self.instance.deadline:
            self.initial["deadline"] = timezone.localtime(self.instance.deadline).date()
        if self.instance.owner_community_id is not None:
            # meta de comunidade: o livro é sempre o da comunidade e é
            # atribuído em GoalService.create_goal, então o campo não aparece
            del self.fields["book"]
        else:
            # livro é opcional: a meta não quebra se ele for excluído
            self.fields["book"].required = False
            self.fields["book"].empty_label = "Nenhum livro"
        # na criação o status é sempre ACTIVE (default do model)
        if not self.instance.pk:
            del self.fields["status"]
        # meta de comunidade: o limite de páginas já é conhecido (livro da
        # comunidade), então o navegador também já avisa pelo atributo max
        self.max_pages = self._community_book_pages()
        if self.max_pages:
            self.fields["target"].widget.attrs["max"] = self.max_pages

    def _community_book_pages(self):
        """Nº de páginas do livro da meta de comunidade (ou None)."""
        if self.instance.owner_community_id is None:
            return None
        # na edição vale o livro gravado na meta; na criação, o da comunidade
        book = self.instance.book or self.instance.owner_community.book
        return book.pages if book else None

    def _page_limit(self, cleaned):
        """(limite, livro) para o alvo de páginas."""
        if self.instance.owner_community_id is not None:
            book = self.instance.book or self.instance.owner_community.book
        else:
            book = cleaned.get("book")
        if book and book.pages:
            return book.pages, book
        return MAX_GOAL_PAGES, None

    def clean_deadline(self):
        deadline = self.cleaned_data.get("deadline")
        if not deadline:
            return None
        # só valida se o prazo foi enviado/alterado; assim editar outros
        # campos de uma meta com prazo já vencido não é bloqueado
        if "deadline" in self.changed_data and deadline < timezone.localdate():
            raise forms.ValidationError("O prazo não pode estar no passado.")
        # o model guarda data e hora: o prazo vale até o fim do dia escolhido
        return timezone.make_aware(
            datetime.combine(deadline, time(23, 59))
        )

    def clean_target_time(self):
        """'1:30' -> 90 minutos. Só dígitos ('2') conta como horas."""
        raw = (self.cleaned_data.get("target_time") or "").strip()
        if not raw:
            return None
        match = re.fullmatch(r"(\d{1,3})(?::([0-5]\d))?", raw)
        if not match:
            raise forms.ValidationError("Use o formato horas:minutos, ex.: 1:30.")
        minutes = int(match.group(1)) * 60 + int(match.group(2) or 0)
        if minutes < 1:
            raise forms.ValidationError("O tempo deve ser maior que zero.")
        return minutes

    def clean(self):
        cleaned = super().clean()
        goal_type = cleaned.get("goal_type")

        if goal_type == Goal.GoalType.HOUR_COUNT:
            if cleaned.get("target_time"):
                cleaned["target"] = cleaned["target_time"]
            elif "target_time" not in self.errors and cleaned.get("target") is None:
                self.add_error("target_time", "Informe o tempo de leitura.")
            # sem target_time mas com target: alvo já em minutos (ex.: testes)

        elif goal_type == Goal.GoalType.PAGE_COUNT and "target" not in self.errors:
            target = cleaned.get("target")
            if target is None:
                self.add_error("target", "Informe a quantidade de páginas.")
            else:
                limit, book = self._page_limit(cleaned)
                if target > limit:
                    self.add_error("target", (
                        f'O livro "{book.title}" tem {limit} páginas; a meta pode ter no máximo isso.'
                        if book else
                        f"A meta pode ter no máximo {limit:,} páginas.".replace(",", ".")
                    ))

        return cleaned


class ReadingSessionForm(forms.ModelForm):
    current_page = forms.IntegerField(
        label="Página atual",
        required=False,
        min_value=1
    )

    current_percentage = forms.DecimalField(
        label="Percentual total lido",
        required=False,
        min_value=0,
        max_value=100,
        decimal_places=2,
        max_digits=5
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user is not None:
            self.instance.user = user

    class Meta:
        model = ReadingSession
        fields = ["book", "minute_count", "date"]

    def clean(self):
        cleaned = super().clean()

        current_page = cleaned.get("current_page")
        current_percentage = cleaned.get("current_percentage")
        book = cleaned.get("book")

        #exige que o usuário escolha apenas uma forma de informar
        if current_page is None and current_percentage is None:
            raise forms.ValidationError(
                "Informe a página atual ou o percentual total lido."
            )

        if current_page is not None and current_percentage is not None:
            raise forms.ValidationError(
                "Informe somente a página atual ou o percentual."
            )

        #verifica se a página atual é válida
        if current_page is not None and book:
            if book.pages is None:
                self.add_error(
                    "book",
                    "O livro precisa ter a quantidade de páginas informada."
                )
            elif current_page > book.pages:
                self.add_error(
                    "current_page",
                    "A página atual não pode ultrapassar o total de páginas do livro."
                )

        return cleaned