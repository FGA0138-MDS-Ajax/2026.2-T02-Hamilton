from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AuditLogFilterForm, AuditLogForm
from .models import AuditLog
from .services import delete_log, log_edit

LOGS_PER_PAGE = 25


def admin_required(view):
    """Só administradores (superusuários) acessam; os demais recebem 403.

    Usuários anônimos são mandados para o login (login_required).
    """

    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseForbidden("Access restricted.")
        return view(request, *args, **kwargs)

    return wrapper


@admin_required
def log_list(request):
    logs = AuditLog.objects.select_related("actor", "content_type")

    filter_form = AuditLogFilterForm(request.GET)
    logs = filter_form.filter(logs)

    page = Paginator(logs, LOGS_PER_PAGE).get_page(request.GET.get("page"))

    # os filtros ativos (sem a página) são repetidos nos links de paginação
    query = request.GET.copy()
    query.pop("page", None)

    return render(request, "logs/log_list.html", {
        "page": page,
        "filter_form": filter_form,
        "query_string": query.urlencode(),
    })


@admin_required
def log_detail(request, log_id):
    log = get_object_or_404(
        AuditLog.objects.select_related("actor", "content_type"),
        id=log_id,
    )
    return render(request, "logs/log_detail.html", {"log": log})


@admin_required
def edit_log(request, log_id):
    log = get_object_or_404(AuditLog, id=log_id)

    # foto tirada antes do formulário: o is_valid() do ModelForm já
    # altera a instância em memória, e precisamos do valor antigo para o log.
    before = log.to_snapshot()

    if request.method == "POST":
        form = AuditLogForm(request.POST, instance=log)

        if form.is_valid():
            form.save()
            # a edição também é registrada (LOG_EDITED)
            log_edit(request.user, log, before)

            messages.success(request, "Log atualizado.")
            return redirect("logs:log_detail", log_id=log.id)
    else:
        form = AuditLogForm(instance=log)

    return render(request, "logs/log_form.html", {"form": form, "log": log})


@admin_required
def delete_log_view(request, log_id):
    log = get_object_or_404(AuditLog, id=log_id)

    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    # a exclusão também é registrada (LOG_DELETED)
    delete_log(request.user, log)

    messages.success(request, "Log excluído.")
    return redirect("logs:log_list")
