"""Regras de negócio das sessões de leitura (ReadingSession).

Tudo que cria ou edita uma sessão passa por `persist_reading_session`, que roda
inteiro numa transação e:

1. valida e posiciona a sessão na linha do tempo do usuário no livro
   (ordem: created_at, id);
2. recalcula `cumulative_*`/`stopped_*` EM CASCATA para todas as sessões do
   usuário no livro (linhas que não mudam não são regravadas);
3. sincroniza o BookStatus (reading_progress, status, finished_at);
4. atualiza a ofensiva (Profile).

Modelo de dados usado no recálculo
- Livro COM total de páginas: `pages_read` é a fonte da verdade; os acumulados
  são a soma de `pages_read` na ordem da linha do tempo (percentual derivado de
  cumulative_pages / book.pages). Informar percentual converte para páginas.
- Livro SEM total de páginas: só `record_type='percent'`; `stopped_percent` é a
  posição absoluta em que o leitor parou e `cumulative_percent` a acompanha.
  Ela precisa ficar estritamente entre a sessão anterior e a seguinte.
"""
import sys
from datetime import datetime, time
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from accounts.models import Profile
from .models import BookStatus, ReadingSession

MAX_SESSION_MINUTES = 1440  # 24h, mesmo limite da tela "Registrar leitura"

PERCENT_STEP = Decimal("0.01")
PROGRESS_STEP = Decimal("0.001")
ZERO_PERCENT = Decimal("0.00")


class ReadingSessionError(Exception):
    """Erro de validação/negócio mostrado ao usuário (vira HTTP 400 ou 404)."""

    def __init__(self, message, field=None, status=400):
        super().__init__(message)
        self.message = message
        self.field = field
        self.status = status


# ---------------------------------------------------------------------------
# Conversões puras (sem banco)
# ---------------------------------------------------------------------------
def percent_to_pages(percent, total_pages):
    """Percentual (0-100) -> página correspondente, arredondando para cima em .5."""
    return int(
        (Decimal(percent) * total_pages / Decimal("100")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )


def pages_to_percent(pages, total_pages):
    """Página acumulada -> percentual com 2 casas (limitado a 100)."""
    value = Decimal(pages) * Decimal("100") / Decimal(total_pages)
    return min(Decimal("100.00"), value.quantize(PERCENT_STEP, rounding=ROUND_HALF_UP))


def compute_timeline(book, sessions):
    """Calcula os acumulados de cada sessão (já ordenadas por created_at, id).

    Devolve uma lista de dicts, um por sessão, com cumulative_pages, stopped_page,
    cumulative_percent e stopped_percent. Não toca no banco.
    """
    timeline = []
    running_pages = 0
    running_percent = ZERO_PERCENT

    for session in sessions:
        if book.pages:
            if session.pages_read is not None:
                running_pages += session.pages_read
            elif session.stopped_percent is not None:
                # sessão antiga em percentual (livro ganhou páginas depois): âncora
                running_pages = percent_to_pages(session.stopped_percent, book.pages)
            running_percent = pages_to_percent(running_pages, book.pages)
            timeline.append({
                "cumulative_pages": running_pages,
                "stopped_page": running_pages,
                "cumulative_percent": running_percent,
                "stopped_percent": running_percent,
            })
        else:
            if session.stopped_percent is not None:
                running_percent = session.stopped_percent
            timeline.append({
                "cumulative_pages": None,
                "stopped_page": None,
                "cumulative_percent": running_percent,
                "stopped_percent": (
                    session.stopped_percent
                    if session.stopped_percent is not None else running_percent
                ),
            })

    return timeline


# ---------------------------------------------------------------------------
# Leitura/validação do payload JSON
# ---------------------------------------------------------------------------
def _parse_int(value, field, label):
    if isinstance(value, bool):
        raise ReadingSessionError(f"{label} inválido.", field)
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if text.lstrip("-").isdigit():
            return int(text)
    raise ReadingSessionError(f"{label} inválido.", field)


def _parse_percent(value, field="stopped_percent"):
    message = "Percentual inválido (use um valor maior que 0 e até 100)."
    if isinstance(value, bool):
        raise ReadingSessionError(message, field)
    try:
        percent = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ReadingSessionError(message, field)
    if not percent.is_finite():
        raise ReadingSessionError(message, field)
    percent = percent.quantize(PERCENT_STEP, rounding=ROUND_HALF_UP)
    if percent <= 0 or percent > 100:
        raise ReadingSessionError(message, field)
    return percent


def parse_created_at(value):
    """Aceita ISO 8601 ('2026-11-10T15:30:00-03:00') ou só a data ('2026-11-10')."""
    message = "Data/hora da sessão inválida (use o formato ISO 8601)."
    if not isinstance(value, str):
        raise ReadingSessionError(message, "created_at")

    text = value.strip()
    try:
        parsed = parse_datetime(text)
        if parsed is None:
            day = parse_date(text)
            parsed = datetime.combine(day, time.min) if day else None
    except ValueError:
        parsed = None
    if parsed is None:
        raise ReadingSessionError(message, "created_at")

    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed)

    if timezone.localdate(parsed) > timezone.localdate():
        raise ReadingSessionError(
            "A data da leitura não pode estar no futuro.", "created_at"
        )
    return parsed


def created_at_from_date(day):
    """created_at para quem só informa a data (form): a data dada + hora atual."""
    now = timezone.localtime()
    return timezone.make_aware(datetime.combine(day, now.time()))


def parse_session_payload(payload, book, existing=None):
    """Valida o corpo JSON de criação (existing=None) ou edição de uma sessão.

    Devolve {record_type, pages_read, stopped_percent, minute_count, created_at};
    na edição, o que não foi enviado vem como None (= manter o valor atual).
    """
    if not isinstance(payload, dict):
        raise ReadingSessionError("Dados da sessão inválidos.")

    record_type = payload.get("record_type")
    pages_raw = payload.get("pages_read")
    percent_raw = payload.get("stopped_percent")
    minutes_raw = payload.get("minute_count")
    created_raw = payload.get("created_at")

    if existing is not None and all(
        value is None
        for value in (record_type, pages_raw, percent_raw, minutes_raw, created_raw)
    ):
        raise ReadingSessionError("Nenhum campo para alterar.")

    has_pages = pages_raw is not None
    has_percent = percent_raw is not None

    # --- record_type ---
    if record_type is None:
        if has_pages and has_percent:
            raise ReadingSessionError("Informe pages_read OU stopped_percent, não os dois.")
        if has_pages:
            record_type = ReadingSession.RecordType.PAGES
        elif has_percent:
            record_type = ReadingSession.RecordType.PERCENT
        elif existing is not None:
            record_type = existing.record_type
        else:
            raise ReadingSessionError("Informe pages_read ou stopped_percent.")
    elif record_type not in ReadingSession.RecordType.values:
        raise ReadingSessionError(
            "record_type inválido (use 'pages' ou 'percent').", "record_type"
        )

    if not book.pages and record_type != ReadingSession.RecordType.PERCENT:
        raise ReadingSessionError(
            "Livros sem total de páginas exigem record_type='percent'.", "record_type"
        )

    if record_type == ReadingSession.RecordType.PAGES and has_percent:
        raise ReadingSessionError(
            "Com record_type='pages' informe pages_read, não stopped_percent.", "stopped_percent"
        )
    if record_type == ReadingSession.RecordType.PERCENT and has_pages:
        raise ReadingSessionError(
            "Com record_type='percent' informe stopped_percent, não pages_read.", "pages_read"
        )

    # --- quantidade ---
    pages_read = None
    stopped_percent = None
    if has_pages:
        pages_read = _parse_int(pages_raw, "pages_read", "Páginas lidas")
        if pages_read < 1:
            raise ReadingSessionError("Informe páginas lidas maiores que zero.", "pages_read")
        if book.pages and pages_read > book.pages:
            raise ReadingSessionError(
                f"As páginas lidas não podem ultrapassar o total do livro ({book.pages}).",
                "pages_read",
            )
    elif has_percent:
        stopped_percent = _parse_percent(percent_raw)
    elif existing is None or record_type != existing.record_type:
        # criação, ou troca de tipo sem informar o novo valor
        raise ReadingSessionError("Informe pages_read ou stopped_percent.")

    # --- tempo ---
    minute_count = None
    if minutes_raw is not None:
        minute_count = _parse_int(minutes_raw, "minute_count", "Tempo da sessão")
        if not 1 <= minute_count <= MAX_SESSION_MINUTES:
            raise ReadingSessionError(
                "O tempo da sessão deve ser de 1 a 1440 minutos (até 24h).", "minute_count"
            )
    elif existing is None:
        raise ReadingSessionError("Informe o tempo da sessão (minute_count).", "minute_count")

    created_at = parse_created_at(created_raw) if created_raw is not None else None

    return {
        "record_type": record_type,
        "pages_read": pages_read,
        "stopped_percent": stopped_percent,
        "minute_count": minute_count,
        "created_at": created_at,
    }


# ---------------------------------------------------------------------------
# Persistência (tudo em transação)
# ---------------------------------------------------------------------------
def _user_sessions(user, book):
    return (
        ReadingSession.objects.select_for_update()
        .filter(user=user, book=book)
        .order_by("created_at", "id")
    )


def _recalculate_timeline(book, sessions):
    """Regrava cumulative_*/stopped_* na ordem da linha do tempo. Só salva o que mudou."""
    timeline = compute_timeline(book, sessions)

    if book.pages and timeline and timeline[-1]["cumulative_pages"] > book.pages:
        raise ReadingSessionError(
            f"A soma das páginas lidas ultrapassa o total do livro ({book.pages}).",
            "pages_read",
        )

    fields = ["cumulative_pages", "stopped_page", "cumulative_percent", "stopped_percent"]
    changed = []
    for session, values in zip(sessions, timeline):
        if any(getattr(session, name) != values[name] for name in fields):
            for name in fields:
                setattr(session, name, values[name])
            changed.append(session)

    if changed:
        ReadingSession.objects.bulk_update(changed, fields)


def _sync_book_status(user, book, last_session):
    """Alinha BookStatus (progresso, status, finished_at) com a última sessão."""
    if book.pages:
        progress = Decimal(last_session.cumulative_pages) / Decimal(book.pages)
    else:
        progress = Decimal(last_session.cumulative_percent) / Decimal("100")
    progress = min(Decimal("1"), progress).quantize(PROGRESS_STEP, rounding=ROUND_HALF_UP)

    book_status, _ = BookStatus.objects.get_or_create(user=user, book=book)
    book_status.reading_progress = progress

    if progress >= 1:
        book_status.status = BookStatus.Status.READ
        if book_status.finished_at is None:
            book_status.finished_at = last_session.date
    else:
        book_status.status = BookStatus.Status.READING
        book_status.finished_at = None

    book_status.save(update_fields=["reading_progress", "status", "finished_at"])
    return book_status


def _rebuild_streak(profile):
    """Refaz a ofensiva do zero a partir de TODOS os dias com leitura do usuário.

    Usado quando o conjunto de dias pode ter mudado (edição de sessão ou sessão
    retroativa): dias que deixaram de existir saem da conta e dias novos entram.
    """
    days = (
        ReadingSession.objects.filter(user=profile.user)
        .order_by("date")
        .values_list("date", flat=True)
        .distinct()
    )

    profile.streak = 0
    profile.last_read_date = None
    for day in days:
        try:
            profile.register_reading_day(day)
        except ValueError:  # dia no futuro (dado inconsistente): ignora
            continue
    profile.reset_streak_if_broken()
    profile.save(update_fields=["streak", "last_read_date"])


def _sync_streak(user, session_date, rebuild):
    profile, _ = Profile.objects.get_or_create(user=user)

    retroactive = (
        profile.last_read_date is not None and session_date < profile.last_read_date
    )
    if rebuild or retroactive:
        _rebuild_streak(profile)
    elif profile.register_reading_day(session_date):
        profile.save(update_fields=["streak", "last_read_date"])
    return profile


def persist_reading_session(user, book, data, session=None, clamp_to_remaining=False):
    """Cria (session=None) ou edita uma sessão e recalcula tudo, numa transação.

    `data` vem de `parse_session_payload` (ou do form). Para livros com páginas,
    `pages_read` informado vale como está; se vier só `stopped_percent`, ele é
    convertido em páginas lidas relativas à sessão anterior na linha do tempo.
    `clamp_to_remaining`: ao ACRESCENTAR no fim, limita pages_read ao que resta do
    livro (arredondamentos do cliente). Levanta ReadingSessionError; como a
    exceção sai do bloco atomic, nada é gravado.

    Devolve dict com session, sessions (histórico atualizado), book_status, profile.
    """
    with transaction.atomic():
        all_sessions = list(_user_sessions(user, book))

        target = None
        if session is not None:
            target = next((s for s in all_sessions if s.pk == session.pk), None)
            if target is None:
                raise ReadingSessionError("Sessão não encontrada.", status=404)
        others = [s for s in all_sessions if target is None or s.pk != target.pk]

        old_date = target.date if target is not None else None
        created_at = data.get("created_at") or (
            target.created_at if target is not None else timezone.now()
        )

        # posição da sessão na linha do tempo (empate de created_at: id decide)
        tie_break = target.pk if target is not None else sys.maxsize
        index = sum(1 for s in others if (s.created_at, s.pk) < (created_at, tie_break))
        before, after = others[:index], others[index:]
        previous = compute_timeline(book, before)[-1] if before else None

        record_type = data["record_type"]
        pages_read = None
        stopped_percent = None

        if book.pages:
            previous_pages = previous["cumulative_pages"] if previous else 0
            if data.get("pages_read") is not None:
                pages_read = data["pages_read"]
            elif data.get("stopped_percent") is not None:
                pages_read = percent_to_pages(data["stopped_percent"], book.pages) - previous_pages
                if pages_read < 1:
                    raise ReadingSessionError(
                        "O progresso informado deve ser maior que o anterior.",
                        "stopped_percent",
                    )
            elif target is not None:
                pages_read = target.pages_read  # edição sem novo valor: mantém
                stopped_percent = target.stopped_percent

            if pages_read is not None:
                if pages_read > book.pages:
                    raise ReadingSessionError(
                        f"As páginas lidas não podem ultrapassar o total do livro ({book.pages}).",
                        "pages_read",
                    )
                remaining = book.pages - previous_pages
                if clamp_to_remaining and target is None and not after and pages_read > remaining:
                    if remaining < 1:
                        raise ReadingSessionError(
                            "Todas as páginas deste livro já foram registradas.", "pages_read"
                        )
                    pages_read = remaining
        else:
            if record_type != ReadingSession.RecordType.PERCENT:
                raise ReadingSessionError(
                    "Livros sem total de páginas exigem record_type='percent'.", "record_type"
                )
            stopped_percent = data.get("stopped_percent")
            if stopped_percent is None and target is not None:
                stopped_percent = target.stopped_percent
            if stopped_percent is None:
                raise ReadingSessionError("Informe stopped_percent.", "stopped_percent")

            previous_percent = previous["cumulative_percent"] if previous else ZERO_PERCENT
            if stopped_percent <= previous_percent:
                raise ReadingSessionError(
                    f"O percentual deve ser maior que o da sessão anterior ({previous_percent}%).",
                    "stopped_percent",
                )
            if after:
                next_session = after[0]
                next_percent = (
                    next_session.stopped_percent
                    if next_session.stopped_percent is not None
                    else next_session.cumulative_percent
                )
                if next_percent is not None and stopped_percent >= next_percent:
                    raise ReadingSessionError(
                        f"O percentual deve ser menor que o da sessão seguinte ({next_percent}%).",
                        "stopped_percent",
                    )

        if target is None:
            target = ReadingSession(user=user, book=book)

        target.record_type = record_type
        target.pages_read = pages_read
        target.stopped_percent = stopped_percent
        if data.get("minute_count") is not None:
            target.minute_count = data["minute_count"]
        target.created_at = created_at
        target.date = timezone.localdate(created_at)
        # valores provisórios (o recálculo abaixo grava os definitivos); também
        # evitam que ReadingSession.save() faça outra consulta para o acumulado
        if book.pages and pages_read is not None:
            target.cumulative_pages = (previous["cumulative_pages"] if previous else 0) + pages_read
            target.stopped_page = target.cumulative_pages

        try:
            target.full_clean()
        except ValidationError as error:
            field = next(iter(error.message_dict), None) if hasattr(error, "error_dict") else None
            raise ReadingSessionError(" ".join(error.messages), field)
        target.save()

        # cascata: reordena e recalcula a linha do tempo inteira (só regrava o que mudou)
        ordered = list(_user_sessions(user, book))
        _recalculate_timeline(book, ordered)

        book_status = _sync_book_status(user, book, ordered[-1])

        # edição: o conjunto de dias pode ter mudado (inclusive perdido o único dia)
        profile = _sync_streak(user, target.date, rebuild=old_date is not None)

        target = next(s for s in ordered if s.pk == target.pk)

    return {
        "session": target,
        "sessions": ordered,
        "book_status": book_status,
        "profile": profile,
    }


# ---------------------------------------------------------------------------
# Serialização (JSON)
# ---------------------------------------------------------------------------
def _number(value):
    return None if value is None else float(value)


def serialize_session(session):
    return {
        "id": session.id,
        "book_id": session.book_id,
        "record_type": session.record_type,
        "pages_read": session.pages_read,
        "minute_count": session.minute_count,
        "stopped_page": session.stopped_page,
        "stopped_percent": _number(session.stopped_percent),
        "cumulative_pages": session.cumulative_pages,
        "cumulative_percent": _number(session.cumulative_percent),
        "date": session.date.isoformat(),
        "created_at": timezone.localtime(session.created_at).isoformat(),
    }


def serialize_book_status(book_status):
    return {
        "status": book_status.status,
        "status_label": book_status.get_status_display(),
        "progress": book_status.progress_percent,
        "reading_progress": float(book_status.reading_progress),
        "finished_at": book_status.finished_at.isoformat() if book_status.finished_at else None,
    }


def build_session_response(result):
    """Corpo JSON de create/edit: a sessão, o histórico atualizado, BookStatus e ofensiva."""
    session = result["session"]
    profile = result["profile"]
    return {
        "success": True,
        # chaves antigas (compatibilidade com o JS atual)
        "id": session.id,
        "pages_read": session.pages_read,
        "minute_count": session.minute_count,
        "date": session.date.isoformat(),
        # novas
        "session": serialize_session(session),
        "sessions": [serialize_session(s) for s in result["sessions"]],
        "book_status": serialize_book_status(result["book_status"]),
        "streak": {
            "current": profile.streak,
            "last_read_date": profile.last_read_date.isoformat() if profile.last_read_date else None,
        },
    }
