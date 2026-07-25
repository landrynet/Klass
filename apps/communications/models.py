"""
Module Communications — Messages et annonces de l'école.
Fil de communication visible dans le portail parents/élèves.
"""
from django.db import models
from apps.core.models import TenantAwareModel
from apps.core.constants import MessageType


class Message(TenantAwareModel):
    """
    Message/annonce de l'école à destination des parents et/ou élèves.
    Visible dans le portail selon le public cible.
    """
    title = models.CharField(max_length=200, verbose_name="Titre")
    body = models.TextField(verbose_name="Contenu")
    message_type = models.CharField(
        max_length=30,
        choices=MessageType.CHOICES,
        default=MessageType.ANNOUNCEMENT,
        verbose_name="Type"
    )
    school_year = models.ForeignKey(
        "school_years.SchoolYear",
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Année scolaire"
    )

    # Expéditeur
    created_by = models.ForeignKey(
        "accounts.User",
        null=True,
        on_delete=models.SET_NULL,
        related_name="messages_sent",
        verbose_name="Envoyé par"
    )

    # Ciblage
    target_all = models.BooleanField(
        default=False,
        verbose_name="Tous les parents/élèves",
        help_text="Si coché, le message est visible par tous."
    )
    target_classrooms = models.ManyToManyField(
        "academics.Classroom",
        blank=True,
        related_name="messages",
        verbose_name="Classes ciblées"
    )
    target_levels = models.ManyToManyField(
        "academics.Level",
        blank=True,
        related_name="messages",
        verbose_name="Niveaux ciblés"
    )

    # Publication
    is_published = models.BooleanField(default=True, verbose_name="Publié")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="Publié le")

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_message_type_display()}] {self.title}"


class MessageRead(TenantAwareModel):
    """Suivi de lecture des messages par les utilisateurs."""
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="reads",
        verbose_name="Message"
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="message_reads",
        verbose_name="Utilisateur"
    )
    read_at = models.DateTimeField(auto_now_add=True, verbose_name="Lu le")

    class Meta:
        verbose_name = "Lecture de message"
        verbose_name_plural = "Lectures de messages"
        unique_together = [["message", "user"]]

    def __str__(self):
        return f"{self.user} a lu: {self.message.title}"
