"""
Module 2 — Paiement Scolaire.
Frais, paiements, reçus et suivi financier.
"""
from django.db import models
from django.core.validators import MinValueValidator
from apps.core.models import TenantAwareModel
from apps.core.constants import FeeType, PaymentMethod
from apps.core.utils import generate_receipt_number


class FeeConfig(TenantAwareModel):
    """
    Configuration des frais scolaires par niveau/option et par type.
    Définie par l'Admin école ou le Comptable en début d'année.
    """
    school_year = models.ForeignKey(
        "school_years.SchoolYear",
        on_delete=models.CASCADE,
        related_name="fee_configs",
        verbose_name="Année scolaire"
    )
    level = models.ForeignKey(
        "academics.Level",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="fee_configs",
        verbose_name="Niveau",
        help_text="Laisser vide pour appliquer à tous les niveaux."
    )
    option = models.ForeignKey(
        "academics.Option",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="fee_configs",
        verbose_name="Option",
        help_text="Laisser vide pour appliquer à toutes les options."
    )
    fee_type = models.CharField(
        max_length=20,
        choices=FeeType.CHOICES,
        verbose_name="Type de frais"
    )
    label = models.CharField(
        max_length=150,
        verbose_name="Libellé",
        help_text="Ex: Frais d'inscription 2025-2026"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Montant (CDF)"
    )
    is_mandatory = models.BooleanField(default=True, verbose_name="Obligatoire")
    due_date = models.DateField(null=True, blank=True, verbose_name="Date d'échéance")

    class Meta:
        verbose_name = "Configuration des frais"
        verbose_name_plural = "Configurations des frais"
        ordering = ["school_year", "fee_type", "label"]

    def __str__(self):
        target = f" — {self.level}" if self.level else ""
        return f"{self.label}{target} ({self.amount} CDF)"


class Payment(TenantAwareModel):
    """
    Enregistrement d'un paiement effectué par un élève/parent.
    Un reçu PDF est généré automatiquement via Celery après chaque paiement.
    """
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Élève"
    )
    school_year = models.ForeignKey(
        "school_years.SchoolYear",
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Année scolaire"
    )
    fee_config = models.ForeignKey(
        FeeConfig,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payments",
        verbose_name="Type de frais"
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Montant payé (CDF)"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.CHOICES,
        default=PaymentMethod.CASH,
        verbose_name="Moyen de paiement"
    )
    payment_date = models.DateField(verbose_name="Date de paiement")
    reference = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name="Référence",
        help_text="Générée automatiquement si laissée vide."
    )
    notes = models.TextField(blank=True, verbose_name="Notes")

    # Audit
    created_by = models.ForeignKey(
        "accounts.User",
        null=True,
        on_delete=models.SET_NULL,
        related_name="payments_recorded",
        verbose_name="Enregistré par"
    )

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ["-payment_date", "-created_at"]

    def __str__(self):
        return f"{self.student} — {self.amount} CDF ({self.payment_date})"

    def save(self, *args, **kwargs):
        if not self.reference:
            # Générer une référence unique
            import uuid
            self.reference = f"PAY-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)


class PaymentReceipt(TenantAwareModel):
    """
    Reçu généré après un paiement.
    La génération PDF est gérée par Celery (tâche asynchrone).
    """
    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name="receipt",
        verbose_name="Paiement"
    )
    receipt_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Numéro de reçu"
    )
    pdf_file = models.FileField(
        upload_to="receipts/",
        null=True,
        blank=True,
        verbose_name="Fichier PDF"
    )
    generated_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Généré le"
    )
    generation_failed = models.BooleanField(
        default=False,
        verbose_name="Échec de génération"
    )

    class Meta:
        verbose_name = "Reçu de paiement"
        verbose_name_plural = "Reçus de paiements"
        ordering = ["-generated_at"]

    def __str__(self):
        return f"Reçu {self.receipt_number} — {self.payment.student}"
