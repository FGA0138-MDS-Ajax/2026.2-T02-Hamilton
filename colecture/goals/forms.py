import json
import re
from datetime import datetime, time

from django import forms
from django.utils import timezone

from .models import GOAL_DESC_MAX_LENGTH, Goal

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


GOAL_EMOJIS = ["📖", "📚", "⏱️", "🌙", "🔥", "🎯", "☕", "🚀"]

WEEKDAY_CHOICES = [
    ("0", "Seg"), ("1", "Ter"), ("2", "Qua"), ("3", "Qui"),
    ("4", "Sex"), ("5", "Sáb"), ("6", "Dom"),
]


class IndividualGoalForm(GoalForm):
    emoji = forms.ChoiceField(
        label="Emoji",
        required=False,
        choices=[("", "Nenhum")] + [(e, e) for e in GOAL_EMOJIS],
    )
    period = forms.ChoiceField(
        label="Frequência",
        required=False,
        choices=Goal.Period.choices,
    )
    weekdays = forms.MultipleChoiceField(
        label="Dias da semana",
        required=False,
        choices=WEEKDAY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta(GoalForm.Meta):
        fields = GoalForm.Meta.fields + ["period", "weekdays", "emoji"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs["placeholder"] = "Ex.: Leitura antes de dormir"
        if self.instance.pk:
            self.initial["weekdays"] = [str(d) for d in self.instance.weekday_list]
        else:
            self.initial["period"] = Goal.Period.DAILY
        self._group_books_by_reading()

    def _group_books_by_reading(self):
        field = self.fields.get("book")
        profile = self.instance.owner_profile
        if field is None or profile is None:
            return
        field.empty_label = "Meta geral (todos os livros)"
        from books.models import BookStatus

        reading_ids = set(
            BookStatus.objects.filter(
                user_id=profile.user_id, status=BookStatus.Status.READING,
            ).values_list("book_id", flat=True)
        )
        books = list(field.queryset.order_by("title"))
        self.book_pages_json = json.dumps(
            {b.pk: b.pages for b in books if b.pages}
        )
        if not reading_ids:
            return
        field.choices = [
            ("", "Meta geral (todos os livros)"),
            ("Lendo", [(b.pk, b.title) for b in books if b.pk in reading_ids]),
            ("Outros livros", [(b.pk, b.title) for b in books if b.pk not in reading_ids]),
        ]

    def clean_period(self):
        return self.cleaned_data.get("period") or Goal.Period.TOTAL

    def clean_weekdays(self):
        days = sorted(set(self.cleaned_data.get("weekdays") or []), key=int)
        return ",".join(days)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("period") == Goal.Period.WEEKDAYS:
            if not cleaned.get("weekdays") and "weekdays" not in self.errors:
                self.add_error("weekdays", "Escolha pelo menos um dia da semana.")
        else:
            cleaned["weekdays"] = ""

        status = cleaned.get("status", self.instance.status)
        profile = self.instance.owner_profile
        if profile is not None and status != Goal.Status.CONCLUDED:
            others = Goal.objects.filter(owner_profile=profile).exclude(
                status=Goal.Status.CONCLUDED
            )
            if self.instance.pk:
                others = others.exclude(pk=self.instance.pk)
            if others.exists():
                raise forms.ValidationError(
                    "Você já tem uma meta ativa. Conclua ou exclua a atual antes de criar outra."
                )
        return cleaned