"""
Tâches Celery pour le module Notifications.
Envoi asynchrone d'emails, SMS, WhatsApp et push.
"""
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(name="notifications.send_notification")
def send_notification(notification_id: int):
    """
    Envoie une notification selon son canal.
    Dispatché selon le canal: email, SMS, push, WhatsApp.
    TODO Phase 9 : Implémentation complète Africa's Talking + VAPID push.
    """
    try:
        from .models import Notification
        from django.utils import timezone

        notification = Notification.objects.get(id=notification_id)

        if notification.channel == "email":
            _send_email_notification(notification)
        elif notification.channel == "sms":
            _send_sms_notification(notification)
        elif notification.channel == "push":
            _send_push_notification(notification)
        elif notification.channel == "whatsapp":
            _send_whatsapp_notification(notification)
        else:
            logger.warning("Canal inconnu: %s", notification.channel)
            return

        notification.status = "sent"
        notification.sent_at = timezone.now()
        notification.save(update_fields=["status", "sent_at"])

        logger.info("Notification %s envoyée via %s", notification_id, notification.channel)

    except Exception as exc:
        logger.error("Erreur envoi notification %s: %s", notification_id, exc)
        try:
            notification.status = "failed"
            notification.error_message = str(exc)
            notification.save(update_fields=["status", "error_message"])
        except Exception:
            pass
        raise


def _send_email_notification(notification):
    """Envoi email via Django mail backend."""
    from django.core.mail import send_mail
    from django.conf import settings

    recipient_email = notification.recipient.email
    if not recipient_email:
        logger.warning("Pas d'email pour l'utilisateur %s", notification.recipient_id)
        return

    send_mail(
        subject=notification.title,
        message=notification.body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient_email],
        fail_silently=False,
    )


def _send_sms_notification(notification):
    """Envoi SMS via Africa's Talking (Phase 9)."""
    logger.info("[STUB] SMS non implémenté — notification %s", notification.id)


def _send_push_notification(notification):
    """Envoi Web Push via VAPID (Phase 7)."""
    logger.info("[STUB] Push non implémenté — notification %s", notification.id)


def _send_whatsapp_notification(notification):
    """Envoi WhatsApp via WhatsApp Business API (Phase 9)."""
    logger.info("[STUB] WhatsApp non implémenté — notification %s", notification.id)
