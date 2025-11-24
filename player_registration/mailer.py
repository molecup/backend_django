from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

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

def send_password_reset_email(reset_request, token):
    subject = "Richiesta reimpostazione password"
    from_email = settings.EMAIL_HOST_USER
    to_email = reset_request.user.email

    context = {
        'user': reset_request.user,
        'reset_link': f"{settings.FRONTEND_URL_BASE}/reset-password?mail={reset_request.user.email}&token={token}",
        'expires_at': reset_request.expires_at,
    }

    text_content = render_to_string('mail/password_reset.txt', context)
    html_content = render_to_string('mail/password_reset.html', context)

    email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=True)

def send_welcome_email(reset_request, token):
    subject = "Benvenuto nel Sistema di Registrazione Giocatori LCS"
    from_email = settings.EMAIL_HOST_USER
    to_email = reset_request.user.email

    context = {
        'user': reset_request.user,
        'reset_link': f"{settings.FRONTEND_URL_BASE}/reset-password?mail={reset_request.user.email}&token={token}",
        'expires_at': reset_request.expires_at,
    }

    text_content = render_to_string('mail/welcome.txt', context)
    html_content = render_to_string('mail/welcome.html', context)

    email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=True)

def send_email_verification_email(verification, token):
    subject = "Verifica il tuo indirizzo email"
    from_email = settings.EMAIL_HOST_USER
    to_email = verification.user.email

    context = {
        'user': verification.user,
        'verification_link': f"{settings.FRONTEND_URL_BASE}/verify-email?mail={verification.user.email}&token={token}",
    }

    text_content = render_to_string('mail/email_verification.txt', context)
    html_content = render_to_string('mail/email_verification.html', context)

    email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=True)