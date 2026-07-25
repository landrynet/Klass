"""
Module 3 — Emploi du Temps.
Créneaux, plannings et détection de conflits.
La contrainte unique_together garantit l'absence de conflits au niveau DB.
"""
from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import TenantAwareModel
from apps.core.constants import WeekDay


class TimeSlot(TenantAwareModel):
    """
    Créneau horaire standard de l'école.
    Ex: Lundi 07h30-09h00, Mardi 09h15-10h45...
    """
    school_year = models.ForeignKey(
        "school_years.SchoolYear",
        on_delete=models.CASCADE,
        related_name="time_slots",
        verbose_name="Année scolaire"
    )
    day = models.CharField(
        max_length=10,
        choices=WeekDay.CHOICES,
        verbose_name="Jour"
    )
    start_time = models.TimeField(verbose_name="Heure de début")
    end_time = models.TimeField(verbose_name="Heure de fin")
    label = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Libellé",
        help_text="Ex: Période 1, Récréation, Déjeuner"
    )
    is_break = models.BooleanField(
        default=False,
        verbose_name="Pause",
        help_text="Cochez pour les récréations/pauses (non assignables)."
    )

    class Meta:
        verbose_name = "Créneau horaire"
        verbose_name_plural = "Créneaux horaires"
        ordering = ["day", "start_time"]
        unique_together = [["school_year", "day", "start_time"]]

    def __str__(self):
        return f"{self.get_day_display()} {self.start_time:%H:%M}-{self.end_time:%H:%M}"

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("L'heure de fin doit être après l'heure de début.")


class Schedule(TenantAwareModel):
    """
    Affectation d'un enseignant à une classe pour une matière dans un créneau et une salle.

    Les contraintes unique_together garantissent :
    - Un enseignant ne peut pas avoir deux cours au même créneau
    - Une classe ne peut pas avoir deux cours au même créneau
    - Une salle ne peut pas accueillir deux cours au même créneau

    C'est la détection de conflits au niveau base de données (Phase 4).
    """
    school_year = models.ForeignKey(
        "school_years.SchoolYear",
        on_delete=models.CASCADE,
        related_name="schedules",
        verbose_name="Année scolaire"
    )
    time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.CASCADE,
        related_name="schedules",
        verbose_name="Créneau"
    )
    classroom = models.ForeignKey(
        "academics.Classroom",
        on_delete=models.CASCADE,
        related_name="schedules",
        verbose_name="Classe"
    )
    teacher = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.CASCADE,
        related_name="schedules",
        verbose_name="Enseignant"
    )
    subject = models.ForeignKey(
        "academics.Subject",
        on_delete=models.CASCADE,
        related_name="schedules",
        verbose_name="Matière"
    )
    room = models.ForeignKey(
        "academics.Room",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="schedules",
        verbose_name="Salle"
    )
    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Cours planifié"
        verbose_name_plural = "Cours planifiés"
        ordering = ["time_slot__day", "time_slot__start_time", "classroom__name"]
        constraints = [
            # Un enseignant ne peut avoir qu'un seul cours par créneau
            models.UniqueConstraint(
                fields=["teacher", "time_slot"],
                name="unique_teacher_per_timeslot",
            ),
            # Une classe ne peut avoir qu'un seul cours par créneau
            models.UniqueConstraint(
                fields=["classroom", "time_slot"],
                name="unique_classroom_per_timeslot",
            ),
        ]

    def __str__(self):
        return f"{self.classroom} — {self.subject} — {self.teacher} ({self.time_slot})"

    def clean(self):
        """Validation supplémentaire : vérifier le conflit de salle."""
        if self.room and self.time_slot_id:
            conflict = Schedule.objects.filter(
                room=self.room,
                time_slot=self.time_slot,
            ).exclude(pk=self.pk)
            if conflict.exists():
                raise ValidationError(
                    f"Conflit de salle : {self.room} est déjà occupée à ce créneau "
                    f"par {conflict.first()}."
                )
