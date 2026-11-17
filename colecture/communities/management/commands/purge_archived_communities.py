from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from communities.models import ARCHIVE_RETENTION_DAYS, Community
from logs.models import AuditLog
from logs.services import create_log


class Command(BaseCommand):
    help = (
        "Exclui as comunidades arquivadas há mais de "
        f"{ARCHIVE_RETENTION_DAYS} dias. Uso: python manage.py purge_archived_communities"
    )

    def handle(self, *args, **options):
        limit = timezone.now() - timedelta(days=ARCHIVE_RETENTION_DAYS)
        expired = Community.objects.filter(
            state=Community.State.ARCHIVED,
            archived_at__lte=limit,
        )

        count = 0
        for community in expired:
            # ação do sistema (sem autor)
            create_log(
                None,
                AuditLog.Action.COMMUNITY_DELETED,
                community,
                metadata={
                    "community_id": community.id,
                    "community_name": community.name,
                    "reason": "archive_retention_expired",
                },
            )
            community.clean_up_and_delete()
            count += 1

        self.stdout.write(self.style.SUCCESS(f"{count} comunidade(s) excluída(s)."))