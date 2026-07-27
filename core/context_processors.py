from core.models import Connection, Message

def notifications_processor(request):
    """Globally injects pending connection requests and unread message counts into templates."""
    if request.user.is_authenticated:
        # Pending connection requests sent to the logged-in user
        pending_connections = Connection.objects.filter(
            receiver=request.user, 
            status='pending'
        ).select_related('sender', 'sender__profile')
        
        # Unread incoming messages
        unread_messages = Message.objects.filter(
            receiver=request.user, 
            is_read=False
        ).select_related('sender', 'sender__profile').order_by('-timestamp')

        total_notifications = pending_connections.count() + unread_messages.count()

        return {
            'pending_connections': pending_connections,
            'unread_messages': unread_messages,
            'total_notification_count': total_notifications,
        }
    
    return {
        'pending_connections': [],
        'unread_messages': [],
        'total_notification_count': 0,
    }