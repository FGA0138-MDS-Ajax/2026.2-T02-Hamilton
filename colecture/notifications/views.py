from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(
        target_user=request.user
    ).order_by('-created_at', '-id')

    data = [
        {
            'id': notification.id,
            'content': notification.content,
            'created_at': notification.created_at,
        }
        for notification in notifications
    ]

    return JsonResponse({'notifications': data})


@login_required
def notification_history(request):
    Notification.objects.filter(
        target_user=request.user,
        is_read=False,
    ).update(is_read=True)

    notifications = Notification.objects.filter(
        target_user=request.user
    ).order_by('-created_at', '-id')
    return render(
        request,
        'notifications/history.html',
        {'notifications': notifications},
    )


@login_required
@require_POST
def mark_notifications_read(request):
    Notification.objects.filter(
        target_user=request.user,
        is_read=False,
    ).update(is_read=True)
    return JsonResponse({'success': True})


@login_required
@require_POST
def hide_notification_from_popup(request, notification_id):
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        target_user=request.user,
    )
    notification.hidden_from_popup = True
    notification.is_read = True
    notification.save(update_fields=['hidden_from_popup', 'is_read'])
    return JsonResponse({'success': True})


@login_required
def dismiss_notification(request, notification_id):
    if request.method == "POST":
        notification = get_object_or_404(Notification, id=notification_id, target_user=request.user)
        notification.delete()

        return JsonResponse({'success': True})
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)
