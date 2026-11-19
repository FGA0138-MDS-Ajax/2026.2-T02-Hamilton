from django.contrib.contenttypes.models import ContentType

from .models import AuditLog


def create_log(actor, action, target, metadata=None):
    """Registra uma ação no log de auditoria.

    - actor: usuário que executou a ação (None quando foi o sistema);
    - action: um valor de AuditLog.Action;
    - target: o objeto afetado (User, Community, Message...). Só a classe e o
      ID são guardados, então o log continua válido se o objeto for apagado
      depois. Para registrar uma exclusão, chame antes de apagar o objeto;
    - metadata: dict com informações extras (precisa ser serializável em JSON).
    """
    return AuditLog.objects.create(
        actor=actor,
        action=action,
        content_type=ContentType.objects.get_for_model(target),
        object_id=target.pk,
        metadata=metadata or {},
    )


def _diff_snapshots(before, after):
    """Campos que mudaram entre duas fotos de um log: {campo: {old, new}}."""
    return {
        field: {"old": before[field], "new": after[field]}
        for field in after
        if before.get(field) != after[field]
    }


def log_edit(admin, log, before):
    """Registra (LOG_EDITED) a edição de um log feita por um administrador.

    `before` é o log.to_snapshot() tirado ANTES de a edição ser aplicada.
    Se nada mudou, nenhum log é criado e retorna None.
    """
    changes = _diff_snapshots(before, log.to_snapshot())
    if not changes:
        return None
    return create_log(
        admin,
        AuditLog.Action.LOG_EDITED,
        log,
        metadata={"changes": changes},
    )


def delete_log(admin, log):
    """Exclui um log e registra (LOG_DELETED) quem o excluiu e o que ele tinha."""
    snapshot = log.to_snapshot()
    log_id = log.pk
    # o alvo do novo log é o log excluído; como só o ID é guardado,
    # o registro continua válido depois do delete.
    entry = create_log(
        admin,
        AuditLog.Action.LOG_DELETED,
        log,
        metadata={"deleted_log": snapshot},
    )
    log.delete()
    return entry
