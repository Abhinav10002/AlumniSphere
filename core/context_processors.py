from core.models import Connection, Message

def notifications_context(request):
    """
    Global context processor to supply unread notifications to the navbar
    across all templates without needing to pass them in every view.
    """
    if request.user.is_authenticated:
        pending_connections = Connection.objects.filter(
            receiver=request.user, 
            status='pending'
        )
        unread_messages = Message.objects.filter(
            receiver=request.user, 
            is_read=False
        )
        total_count = pending_connections.count() + unread_messages.count()
        return {
            'pending_connections': pending_connections,
            'unread_messages': unread_messages,
            'total_notification_count': total_count,
        }
    
    return {
        'pending_connections': [],
        'unread_messages': [],
        'total_notification_count': 0,
    }