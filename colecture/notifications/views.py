from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import Notification
from django.http import JsonResponse
# Create your views here.

@login_required
def notification_list(request):
    notifications = Notification.objects.filter(target_user=request.user)

    data = [
        {
            'id': notification.id,
            'content': notification.content,
            'created_at': notification.created_at,
        }
        for notification in notifications
    ]

    return JsonResponse({'notifications':data})

@login_required
def dismiss_notification(request, notification_id):
    if request.method == "POST":
        notification = get_object_or_404(Notification, id=notification_id, target_user=request.user)
        notification.delete()

        return JsonResponse({'success':True})
    else:
        return JsonResponse({'error':'Method not allowed'}, status=405)
        
