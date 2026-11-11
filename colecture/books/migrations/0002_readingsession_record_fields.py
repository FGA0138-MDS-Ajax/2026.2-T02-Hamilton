import datetime
from collections import defaultdict

import django.core.validators
import django.utils.timezone
from django.db import migrations, models


def backfill_reading_sessions(apps, schema_editor):
    """Preenche as sessões já existentes (sem apagar nem recriar nada).

    - created_at  <- date à meia-noite (fuso do projeto), para ficar ordenável;
    - record_type <- 'pages';
    - cumulative_pages <- soma acumulada por (user, book), ordenada por (date, id);
    - stopped_page <- cumulative_pages.
    """
    ReadingSession = apps.get_model("books", "ReadingSession")

    totals = defaultdict(int)
    sessions = ReadingSession.objects.order_by("date", "id").iterator()

    for session in sessions:
        key = (session.user_id, session.book_id)
        totals[key] += session.pages_read or 0

        created_at = datetime.datetime.combine(session.date, datetime.time.min)
        if django.utils.timezone.is_naive(created_at):
            created_at = django.utils.timezone.make_aware(created_at)

        # update() evita disparar save() e não mexe em outros campos
        ReadingSession.objects.filter(pk=session.pk).update(
            created_at=created_at,
            record_type="pages",
            cumulative_pages=totals[key],
            stopped_page=totals[key],
        )


def noop_reverse(apps, schema_editor):
    # Campos novos são removidos pelas operações reversas; nada a desfazer nos dados.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="readingsession",
            name="pages_read",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                validators=[django.core.validators.MinValueValidator(1)],
            ),
        ),
        migrations.AddField(
            model_name="readingsession",
            name="created_at",
            field=models.DateTimeField(
                db_index=True, default=django.utils.timezone.now
            ),
        ),
        migrations.AddField(
            model_name="readingsession",
            name="record_type",
            field=models.CharField(
                choices=[("pages", "Páginas"), ("percent", "Percentual")],
                default="pages",
                max_length=7,
            ),
        ),
        migrations.AddField(
            model_name="readingsession",
            name="stopped_page",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="readingsession",
            name="stopped_percent",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=5,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(100),
                ],
            ),
        ),
        migrations.AddField(
            model_name="readingsession",
            name="cumulative_pages",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="readingsession",
            name="cumulative_percent",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=5,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(100),
                ],
            ),
        ),
        migrations.RunPython(backfill_reading_sessions, noop_reverse),
    ]
