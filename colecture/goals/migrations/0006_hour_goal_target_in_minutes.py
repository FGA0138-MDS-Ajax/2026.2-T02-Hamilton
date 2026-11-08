"""Metas de tempo passam a guardar o alvo em minutos (antes: horas)."""

from django.db import migrations
from django.db.models import F


def hours_to_minutes(apps, schema_editor):
    Goal = apps.get_model("goals", "Goal")
    Goal.objects.filter(goal_type="HOUR_COUNT").update(target=F("target") * 60)


def minutes_to_hours(apps, schema_editor):
    Goal = apps.get_model("goals", "Goal")
    # arredonda para cima para o alvo nunca virar 0
    for goal in Goal.objects.filter(goal_type="HOUR_COUNT"):
        goal.target = max(1, -(-goal.target // 60))
        goal.save(update_fields=["target"])


class Migration(migrations.Migration):

    dependencies = [
        ("goals", "0005_goal_description_alter_goal_goal_type_and_more"),
    ]

    operations = [
        migrations.RunPython(hours_to_minutes, minutes_to_hours),
    ]
