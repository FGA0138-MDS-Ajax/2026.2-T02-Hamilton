from django.db import migrations

# mesmo limite de forums.models.FORUM_NAME_MAX_LENGTH (uma migration
# não deve importar o model atual, só o estado histórico dele)
FORUM_NAME_MAX_LENGTH = 100


def create_missing_forums(apps, schema_editor):
    """
    Cria o fórum geral das comunidades e o fórum das metas coletivas
    que já existiam antes de os fóruns serem criados automaticamente.
    Metas individuais (owner_profile) não têm fórum.
    """
    Community = apps.get_model("communities", "Community")
    Goal = apps.get_model("goals", "Goal")
    Forum = apps.get_model("forums", "Forum")

    for community in Community.objects.filter(forum__isnull=True):
        Forum.objects.create(
            name=(community.name + " Forum")[:FORUM_NAME_MAX_LENGTH],
            community=community,
        )

    for goal in Goal.objects.filter(owner_community__isnull=False, forum__isnull=True):
        Forum.objects.create(
            name=goal.name[:FORUM_NAME_MAX_LENGTH],
            goal=goal,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('communities', '0003_community_archived_at_community_book'),
        ('forums', '0004_alter_forum_community_alter_forum_goal'),
        ('goals', '0005_goal_description_alter_goal_goal_type_and_more'),
    ]

    operations = [
        # sem reversão: apagar os fóruns criados aqui também apagaria
        # mensagens, então desfazer a migration não remove nada.
        migrations.RunPython(create_missing_forums, migrations.RunPython.noop),
    ]