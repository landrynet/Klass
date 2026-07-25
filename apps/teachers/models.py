"""
Module 4 — Gestion du Personnel Enseignant.
Profils enseignants, matières, disponibilités et affectations.
"""
from django.db import models, transaction
from django.utils import timezone
from apps.core.models import TenantAwareModel
from apps.core.constants import Gender, StaffStatus, StaffType


class PersonnelNumberConfiguration(TenantAwareModel):
    """Compteur tenant pour les matricules professionnels."""
    next_number = models.PositiveIntegerField(default=1, verbose_name="Prochain numéro")

    class Meta:
        verbose_name = "Configuration des matricules du personnel"
        verbose_name_plural = "Configuration des matricules du personnel"

    def format_number(self, staff_type, number):
        prefix = "ENS" if staff_type == StaffType.TEACHER else "PER"
        return f"{prefix}-{timezone.now().year}-{number:04d}"


class Personnel(TenantAwareModel):
    """Dossier permanent d'un membre du personnel, indépendant d'un compte."""
    employee_id = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
        verbose_name="Matricule du personnel",
        help_text="Généré automatiquement par KLASS.",
    )
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    gender = models.CharField(max_length=1, choices=Gender.CHOICES, blank=True, verbose_name="Genre")
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Date de naissance")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    email = models.EmailField(blank=True, verbose_name="Email")
    address = models.TextField(blank=True, verbose_name="Adresse")
    specialization = models.CharField(max_length=200, blank=True, verbose_name="Spécialité")
    staff_type = models.CharField(
        max_length=20, choices=StaffType.CHOICES, default=StaffType.OTHER, verbose_name="Type de personnel"
    )
    status = models.CharField(
        max_length=20, choices=StaffStatus.CHOICES, default=StaffStatus.ACTIVE, verbose_name="Statut"
    )
    education_level = models.CharField(max_length=150, blank=True, verbose_name="Niveau d'étude")
    diploma = models.CharField(max_length=200, blank=True, verbose_name="Diplôme")
    experience_years = models.PositiveSmallIntegerField(default=0, verbose_name="Années d'expérience")
    hire_date = models.DateField(null=True, blank=True, verbose_name="Date d'embauche")
    contract_type = models.CharField(
        max_length=30,
        choices=[
            ("permanent", "Permanent"),
            ("temporary", "Temporaire"),
            ("volunteer", "Bénévole"),
        ],
        default="permanent",
        verbose_name="Type de contrat",
    )
    user = models.OneToOneField(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="personnel_profile",
        verbose_name="Compte de connexion",
    )
    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Membre du personnel"
        verbose_name_plural = "Membres du personnel"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.employee_id})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def status_badge_class(self):
        return StaffStatus.BADGE_CLASSES.get(self.status, "bg-secondary-subtle text-secondary")

    @property
    def is_archived(self):
        return self.status == StaffStatus.ARCHIVED

    def save(self, *args, **kwargs):
        if not self.employee_id:
            with transaction.atomic():
                config, _ = PersonnelNumberConfiguration.objects.get_or_create(pk=1)
                config = PersonnelNumberConfiguration.objects.select_for_update().get(pk=config.pk)
                self.employee_id = config.format_number(self.staff_type, config.next_number)
                config.next_number += 1
                config.save(update_fields=["next_number", "updated_at"])
                return super().save(*args, **kwargs)
        return super().save(*args, **kwargs)


class Teacher(TenantAwareModel):
    """
    Profil enseignant — lié au compte utilisateur (rôle teacher).
    Les affectations sont liées à l'année scolaire via TeacherAssignment.
    """
    personnel = models.OneToOneField(
        Personnel,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="teacher_profile",
        verbose_name="Dossier personnel",
    )
    user = models.OneToOneField(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
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
        return f"Prof. {self.full_name}"

    @property
    def full_name(self):
        if self.personnel_id:
            return self.personnel.full_name
        return self.user.get_full_name() if self.user_id else "Enseignant"

    @property
    def email(self):
        if self.personnel_id and self.personnel.email:
            return self.personnel.email
        return self.user.email if self.user_id else ""

    def save(self, *args, **kwargs):
        if self.personnel_id:
            self.employee_id = self.personnel.employee_id
            if not self.specialization:
                self.specialization = self.personnel.specialization
            if not self.phone:
                self.phone = self.personnel.phone
        return super().save(*args, **kwargs)


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
