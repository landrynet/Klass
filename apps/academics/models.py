"""
Module 6 — Gestion des Classes, Niveaux, Options & Salles.
Fondation structurelle de KLASS : tout s'appuie sur ces modèles.
"""
from django.db import models
from django.core.validators import MinValueValidator
from apps.core.models import TenantAwareModel


class Level(TenantAwareModel):
    """
    Niveau scolaire (ex: 6ème, 5ème, 4ème, 3ème, Terminale...).
    Spécifique à chaque école car les nomenclatures varient.
    """
    school_year = models.ForeignKey(
        "school_years.SchoolYear",
        on_delete=models.CASCADE,
        related_name="levels",
        verbose_name="Année scolaire"
    )
    name = models.CharField(max_length=100, verbose_name="Nom du niveau")
    code = models.CharField(max_length=10, blank=True, verbose_name="Code")
    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Ordre d'affichage",
        help_text="0 = premier niveau, croissant"
    )

    class Meta:
        verbose_name = "Niveau"
        verbose_name_plural = "Niveaux"
        ordering = ["order", "name"]
        unique_together = [["school_year", "name"]]

    def __str__(self):
        return f"{self.name} ({self.school_year.name})"


class Option(TenantAwareModel):
    """
    Option / Filière au sein d'un niveau (ex: Scientifique, Littéraire, Technique...).
    """
    level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name="options",
        verbose_name="Niveau"
    )
    name = models.CharField(max_length=100, verbose_name="Nom de l'option")
    code = models.CharField(max_length=10, blank=True, verbose_name="Code")
    description = models.TextField(blank=True, verbose_name="Description")

    class Meta:
        verbose_name = "Option / Filière"
        verbose_name_plural = "Options / Filières"
        ordering = ["level", "name"]
        unique_together = [["level", "name"]]

    def __str__(self):
        return f"{self.level.name} — {self.name}"


class Subject(TenantAwareModel):
    """
    Matière enseignée (ex: Mathématiques, Français, Sciences...).
    Associée à des niveaux via SubjectLevel.
    """
    name = models.CharField(max_length=150, verbose_name="Nom de la matière")
    code = models.CharField(max_length=10, blank=True, verbose_name="Code")
    description = models.TextField(blank=True, verbose_name="Description")
    levels = models.ManyToManyField(
        Level,
        through="SubjectLevel",
        related_name="subjects",
        verbose_name="Niveaux"
    )

    class Meta:
        verbose_name = "Matière"
        verbose_name_plural = "Matières"
        ordering = ["name"]

    def __str__(self):
        return self.name


class SubjectLevel(TenantAwareModel):
    """Association Matière ↔ Niveau avec le volume horaire hebdomadaire."""
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    weekly_hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=1,
        validators=[MinValueValidator(0.5)],
        verbose_name="Heures/semaine"
    )
    is_mandatory = models.BooleanField(default=True, verbose_name="Obligatoire")

    class Meta:
        verbose_name = "Matière par niveau"
        unique_together = [["subject", "level"]]


class Classroom(TenantAwareModel):
    """
    Classe scolaire = Niveau + Option + Identifiant (ex: 4ème Scientifique A).
    Contient les élèves pour une année scolaire donnée.
    """
    school_year = models.ForeignKey(
        "school_years.SchoolYear",
        on_delete=models.CASCADE,
        related_name="classrooms",
        verbose_name="Année scolaire"
    )
    option = models.ForeignKey(
        Option,
        on_delete=models.CASCADE,
        related_name="classrooms",
        verbose_name="Option"
    )
    name = models.CharField(
        max_length=50,
        verbose_name="Nom de la classe",
        help_text="Ex: A, B, ou Classe 1"
    )
    capacity = models.PositiveSmallIntegerField(
        default=40,
        validators=[MinValueValidator(1)],
        verbose_name="Capacité (élèves)"
    )
    main_room = models.ForeignKey(
        "Room",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="main_classrooms",
        verbose_name="Salle principale"
    )

    class Meta:
        verbose_name = "Classe"
        verbose_name_plural = "Classes"
        ordering = ["school_year", "option__level__order", "name"]
        unique_together = [["school_year", "option", "name"]]

    def __str__(self):
        return f"{self.option} — {self.name} ({self.school_year.name})"

    @property
    def full_name(self):
        return f"{self.option.level.name} {self.option.name} {self.name}"


class Room(TenantAwareModel):
    """
    Salle physique de l'établissement (classe, laboratoire, salle info...).
    Utilisée par le module Emploi du Temps pour détecter les conflits.
    """
    ROOM_TYPES = [
        ("classroom", "Salle de classe"),
        ("laboratory", "Laboratoire"),
        ("computer_lab", "Salle informatique"),
        ("library", "Bibliothèque"),
        ("gymnasium", "Gymnase"),
        ("other", "Autre"),
    ]

    name = models.CharField(max_length=100, verbose_name="Nom / Numéro de salle")
    room_type = models.CharField(
        max_length=20,
        choices=ROOM_TYPES,
        default="classroom",
        verbose_name="Type"
    )
    capacity = models.PositiveSmallIntegerField(
        default=40,
        validators=[MinValueValidator(1)],
        verbose_name="Capacité"
    )
    equipment = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Équipements",
        help_text="Liste JSON des équipements disponibles (ex: ['projecteur', 'tableau'])"
    )
    is_available = models.BooleanField(
        default=True,
        verbose_name="Disponible",
        help_text="Décochez si la salle est temporairement hors service."
    )
    floor = models.CharField(max_length=20, blank=True, verbose_name="Étage / Bâtiment")
    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Salle"
        verbose_name_plural = "Salles"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_room_type_display()}, {self.capacity} places)"
