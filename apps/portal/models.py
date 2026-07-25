"""
Module 7 — Portail Parents/Élève (PWA).
Le portail n'a pas de modèles propres : il agrège en lecture
les données des autres modules (paiements, emploi du temps, ressources).

Ce fichier contient uniquement le modèle de notification push (futur).
"""
from django.db import models
from apps.core.models import TenantAwareModel


class PushSubscription(TenantAwareModel):
    """
    Abonnement aux notifications push PWA d'un utilisateur.
    Stocke le endpoint et les clés pour envoyer des notifications Web Push.
    Utilisé dans la Phase 7 pour les alertes en temps réel.
    """
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="push_subscriptions",
        verbose_name="Utilisateur"
    )
    endpoint = models.URLField(max_length=500, verbose_name="Endpoint")
    p256dh = models.CharField(max_length=200, verbose_name="Clé p256dh")
    auth = models.CharField(max_length=50, verbose_name="Auth")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")

    class Meta:
        verbose_name = "Abonnement push"
        verbose_name_plural = "Abonnements push"
        unique_together = [["user", "endpoint"]]

    def __str__(self):
        return f"Push — {self.user} ({self.endpoint[:50]}...)"
