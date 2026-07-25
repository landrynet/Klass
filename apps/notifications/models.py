"""
Module Notifications — Alertes, SMS, email et push notifications.
Canal de communication asynchrone (Celery) vers les parents et élèves.
"""
from django.db import models
from apps.core.models import TenantAwareModel


class Notification(TenantAwareModel):
    """
    Notification envoyée à un utilisateur du portail.
    Gère les canaux : in-app, email, SMS, WhatsApp, push.
    """
    CHANNELS = [
        ("in_app", "In-App (portail)"),
        ("email", "Email"),
        ("sms", "SMS"),
        ("whatsapp", "WhatsApp"),
        ("push", "Notification Push"),
    ]

    STATUS = [
        ("pending", "En attente"),
        ("sent", "Envoyée"),
        ("failed", "Échouée"),
        ("read", "Lue"),
    ]

    recipient = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Destinataire"
    )
    channel = models.CharField(max_length=20, choices=CHANNELS, verbose_name="Canal")
    title = models.CharField(max_length=200, verbose_name="Titre")
    body = models.TextField(verbose_name="Contenu")
    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="pending",
        verbose_name="Statut"
    )

    # Lien vers l'objet source (paiement, message, etc.) — optionnel
    related_message = models.ForeignKey(
        "communications.Message",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="notifications",
        verbose_name="Message associé"
    )

    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Envoyée le")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Lue le")
    error_message = models.TextField(blank=True, verbose_name="Erreur")

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.channel}] {self.title} → {self.recipient}"
