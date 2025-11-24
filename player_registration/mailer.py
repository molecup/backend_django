from django.core.mail import send_mail
from django.conf import settings

def send_deletion_request_notification(deletion_request):
    subject = f"Player Deletion Request: {deletion_request.player_to_be_deleted.user.email}"
    message = f"""
    A deletion request has been submitted for the player with email: {deletion_request.player_to_be_deleted.user.email}
    Player list : {deletion_request.player_to_be_deleted.player_list.name}

    Requested by: {deletion_request.requested_by.email}
    Requested at: {deletion_request.requested_at}

    Please review and process this request in the admin panel.
    """
    from_email = settings.EMAIL_HOST_USER
    recipient_list = settings.EMAIL_NOTIFICATIONS_ADDRESS
    send_mail(subject, message, from_email, recipient_list, fail_silently=True)