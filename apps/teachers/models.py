"""
Module 4 — Gestion du Personnel Enseignant.
Profils enseignants, matières, disponibilités et affectations.
"""
from django.db import models
from apps.core.models import TenantAwareModel


class Teacher(TenantAwareModel):
    """
    Profil enseignant — lié au compte utilisateur (rôle teacher).
    Les affectations sont liées à l'année scolaire via TeacherAssignment.
    """
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="teacher_profile",
        verbose_name="Compte utilisateur"
    )
    employee_id = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
        verbose_name="Matricule employé"
    )
    specialization = models.TextField(blank=True, verbose_name="Spécialisation")
    hire_date = models.DateField(null=True, blank=True, verbose_name="Date d'embauche")
    contract_type = models.CharField(
        max_length=30,
        choices=[
            ("permanent", "Permanent"),
            ("temporary", "Temporaire"),
            ("volunteer", "Bénévole"),
        ],
        default="permanent",
        verbose_name="Type de contrat"
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    bio = models.TextField(blank=True, verbose_name="Biographie")

    # Matières que l'enseignant peut enseigner
    subjects = models.ManyToManyField(
        "academics.Subject",
        through="TeacherSubject",
        related_name="teachers",
        verbose_name="Matières enseignées"
    )

    class Meta:
        verbose_name = "Enseignant"
        verbose_name_plural = "Enseignants"
        ordering = ["user__last_name", "user__first_name"]

    def __str__(self):
        return f"Prof. {self.user.get_full_name()}"

    @property
    def full_name(self):
        return self.user.get_full_name()

    @property
    def email(self):
        return self.user.email


class TeacherSubject(TenantAwareModel):
    """
    Qualification d'un enseignant pour une matière à un niveau donné.
    Utilisé pour les affectations dans l'emploi du temps.
    """
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="subject_qualifications")
    subject = models.ForeignKey("academics.Subject", on_delete=models.CASCADE, related_name="teacher_qualifications")
    level = models.ForeignKey(
        "academics.Level",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Niveau",
        help_text="Laisser vide = toutes les niveaux pour cette matière."
    )
    is_primary = models.BooleanField(
        default=True,
        verbose_name="Matière principale",
        help_text="Distingue la matière principale des matières secondaires."
    )

    class Meta:
        verbose_name = "Qualification enseignant"
        verbose_name_plural = "Qualifications enseignants"
        unique_together = [["teacher", "subject", "level"]]

    def __str__(self):
        level_info = f" — {self.level}" if self.level else ""
        return f"{self.teacher} → {self.subject}{level_info}"


class TeacherAvailability(TenantAwareModel):
    """
    Disponibilités hebdomadaires d'un enseignant.
    Utilisé par le module Emploi du Temps pour les affectations.
    """
    from apps.core.constants import WeekDay

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="availabilities",
        verbose_name="Enseignant"
    )
    school_year = models.ForeignKey(
        "school_years.SchoolYear",
        on_delete=models.CASCADE,
        related_name="teacher_availabilities",
        verbose_name="Année scolaire"
    )
    day = models.CharField(
        max_length=10,
        choices=WeekDay.CHOICES,
        verbose_name="Jour"
    )
    start_time = models.TimeField(verbose_name="Heure de début")
    end_time = models.TimeField(verbose_name="Heure de fin")
    is_available = models.BooleanField(default=True, verbose_name="Disponible")

    class Meta:
        verbose_name = "Disponibilité enseignant"
        verbose_name_plural = "Disponibilités enseignants"
        ordering = ["teacher", "day", "start_time"]
        unique_together = [["teacher", "school_year", "day", "start_time"]]

    def __str__(self):
        status = "Disponible" if self.is_available else "Indisponible"
        return f"{self.teacher} — {self.get_day_display()} {self.start_time}-{self.end_time} ({status})"
