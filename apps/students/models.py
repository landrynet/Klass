"""
Phase 3.0 — Élèves, parents et matricules.
Le dossier élève est permanent; les inscriptions restent prêtes pour la phase 3.1.
"""
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.core.models import TenantAwareModel
from apps.core.constants import Gender, EnrollmentStatus


class Student(TenantAwareModel):
    """
    Dossier permanent d'un élève — persiste d'une année à l'autre.
    L'identité, l'historique et les contacts sont conservés.
    Seule l'inscription (StudentEnrollment) change chaque année.
    """
    # Identifiant unique
    matricule = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Matricule",
        help_text="Généré automatiquement par KLASS."
    )

    # Identité
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    date_of_birth = models.DateField(verbose_name="Date de naissance")
    place_of_birth = models.CharField(max_length=150, blank=True, verbose_name="Lieu de naissance")
    gender = models.CharField(
        max_length=1,
        choices=Gender.CHOICES,
        verbose_name="Genre"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "Actif"),
            ("inactive", "Inactif"),
            ("archived", "Archivé"),
        ],
        default="active",
        verbose_name="Statut",
    )
    primary_parent = models.ForeignKey(
        "Parent",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="primary_students",
        verbose_name="Parent / tuteur principal",
        help_text="Obligatoire lors de la création d'un élève.",
    )
    nationality = models.CharField(max_length=100, default="Congolaise", verbose_name="Nationalité")
    photo = models.ImageField(
        upload_to="students/photos/",
        null=True,
        blank=True,
        verbose_name="Photo"
    )

    # Compte élève (optionnel — pour accès au portail)
    user = models.OneToOneField(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="student_profile",
        verbose_name="Compte utilisateur"
    )

    # Informations médicales/urgences
    blood_type = models.CharField(max_length=5, blank=True, verbose_name="Groupe sanguin")
    medical_notes = models.TextField(blank=True, verbose_name="Notes médicales")
    emergency_contact = models.CharField(max_length=100, blank=True, verbose_name="Contact d'urgence")
    emergency_phone = models.CharField(max_length=20, blank=True, verbose_name="Tél. d'urgence")

    class Meta:
        verbose_name = "Élève"
        verbose_name_plural = "Élèves"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.matricule})"

    def save(self, *args, **kwargs):
        if not self.primary_parent_id:
            raise ValidationError("Un élève doit avoir un parent ou tuteur principal.")
        # Le matricule est réservé sous verrou afin de rester unique lors de
        # créations simultanées. Les anciens matricules ne sont jamais réutilisés.
        if not self.matricule:
            with transaction.atomic():
                config, _ = MatriculeConfiguration.objects.get_or_create(pk=1)
                config = MatriculeConfiguration.objects.select_for_update().get(pk=config.pk)
                while True:
                    number = config.next_number
                    self.matricule = config.format_number(number)
                    config.next_number = number + 1
                    if not Student.objects.filter(matricule=self.matricule).exists():
                        config.save(update_fields=["next_number", "updated_at"])
                        super().save(*args, **kwargs)
                        break
            return
        super().save(*args, **kwargs)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def current_enrollment(self):
        """Retourne l'inscription active de l'élève."""
        return self.enrollments.filter(
            school_year__is_active=True
        ).select_related("classroom", "school_year").first()


class StudentEnrollment(TenantAwareModel):
    """
    Inscription d'un élève pour une année scolaire donnée.
    Créée à chaque nouvelle année (ou lors d'un transfert de classe).
    Archivée (lecture seule) à la clôture de l'année.
    """
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="Élève"
    )
    school_year = models.ForeignKey(
        "school_years.SchoolYear",
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="Année scolaire"
    )
    classroom = models.ForeignKey(
        "academics.Classroom",
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="Classe"
    )
    status = models.CharField(
        max_length=20,
        choices=EnrollmentStatus.CHOICES,
        default=EnrollmentStatus.ACTIVE,
        verbose_name="Statut"
    )
    enrollment_date = models.DateField(
        auto_now_add=True,
        verbose_name="Date d'inscription"
    )
    enrolled_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="enrollments_created",
        verbose_name="Inscrit par"
    )
    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Inscription"
        verbose_name_plural = "Inscriptions"
        ordering = ["-school_year__start_date", "student__last_name"]
        unique_together = [["student", "school_year"]]

    def __str__(self):
        return f"{self.student} — {self.classroom} ({self.school_year.name})"


class Parent(TenantAwareModel):
    """
    Parent ou tuteur légal d'un ou plusieurs élèves.
    Peut avoir un compte pour accéder au portail.
    """
    # Compte portail (optionnel)
    user = models.OneToOneField(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="parent_profile",
        verbose_name="Compte utilisateur"
    )

    # Identité
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    gender = models.CharField(max_length=1, choices=Gender.CHOICES, blank=True)
    phone = models.CharField(max_length=20, verbose_name="Téléphone principal")
    phone_secondary = models.CharField(max_length=20, blank=True, verbose_name="Téléphone secondaire")
    email = models.EmailField(blank=True, verbose_name="Email")
    address = models.TextField(blank=True, verbose_name="Adresse")
    profession = models.CharField(max_length=150, blank=True, verbose_name="Profession")

    # Lien avec les élèves
    students = models.ManyToManyField(
        Student,
        through="ParentStudent",
        related_name="parents",
        verbose_name="Enfants"
    )

    class Meta:
        verbose_name = "Parent / Tuteur"
        verbose_name_plural = "Parents / Tuteurs"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class ParentStudent(TenantAwareModel):
    """Relation Parent ↔ Élève avec type de lien."""
    RELATIONSHIP_CHOICES = [
        ("father", "Père"),
        ("mother", "Mère"),
        ("guardian", "Tuteur légal"),
        ("other", "Autre"),
    ]
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name="children_links")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="parent_links")
    relationship = models.CharField(
        max_length=20,
        choices=RELATIONSHIP_CHOICES,
        default="guardian",
        verbose_name="Lien de parenté"
    )
    is_emergency_contact = models.BooleanField(default=False, verbose_name="Contact d'urgence")
    is_authorized_pickup = models.BooleanField(default=True, verbose_name="Autorisé à récupérer l'enfant")

    class Meta:
        verbose_name = "Lien Parent-Élève"
        verbose_name_plural = "Liens Parent-Élève"
        unique_together = [["parent", "student"]]

    def __str__(self):
        return f"{self.parent} → {self.student} ({self.get_relationship_display()})"


class MatriculeConfiguration(TenantAwareModel):
    """Configuration du format et compteur des matricules d'une école."""
    prefix = models.CharField(max_length=10, default="KLS", verbose_name="Préfixe")
    include_year = models.BooleanField(default=True, verbose_name="Inclure l'année")
    separator = models.CharField(max_length=1, default="-", verbose_name="Séparateur")
    number_digits = models.PositiveSmallIntegerField(default=4, verbose_name="Nombre de chiffres")
    next_number = models.PositiveIntegerField(default=1, verbose_name="Prochain numéro")

    class Meta:
        verbose_name = "Configuration des matricules"
        verbose_name_plural = "Configuration des matricules"

    def __str__(self):
        return self.preview()

    def format_number(self, number):
        parts = [self.prefix.upper()]
        if self.include_year:
            parts.append(str(timezone.now().year))
        parts.append(str(number).zfill(self.number_digits))
        return self.separator.join(parts)

    def preview(self):
        return self.format_number(self.next_number)
