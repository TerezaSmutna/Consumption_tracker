import logging
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.db import DatabaseError
from django.shortcuts import render

# from evidence_spotreby.perms import assign_perm, get_objects_for_user, remove_perm

from django_otp.plugins.otp_totp.models import TOTPDevice


logger = logging.getLogger(__name__)


def has_2fa(user):
    return TOTPDevice.objects.filter(user=user, confirmed=True).exists()


def send_email_and_handle_messages(request, user):
    try:
        send_verification_email(request, to_user=user)
        messages.success(request, f'Verification email sent to {user.email}')
        logger.info(f'Verification email sent to {user.email}')
    except Exception as e:
        logger.error(e)
        messages.error(request, 'Unable to send email. Please contact the administrator.')


def send_verification_email(request, *, to_user=None, flag=None):
    if to_user.is_active:
        to_user.is_active = False
        to_user.save()
    try:
        logger.info(f'Sending {flag or ""} email to {to_user}')
        build_and_send_email(request, to_user)
        return to_user
    except Exception:
        if flag == 'invite':
            to_user.delete()
        raise


def build_and_send_email(request, to_user):
    verification_path = to_user.get_account_verification_path()
    verification_url = request.build_absolute_uri(verification_path)

    send_mail(
        subject='Evidence Spotreby Verification',
        message=f'To activate your account click on this link:\n'
                f'{verification_url}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_user.email],
        fail_silently=False,
    )


def render_error(request, msg, status, domain, user_domains):
    return render(
        request,
        template_name='users/email_verification_failed.html',
        context={
            'msg': msg,
            'status': status,
            'domain': domain,
            'user_domains': user_domains
        }
    )
