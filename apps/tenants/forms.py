"""
Formulaires pour la gestion des tenants (écoles) dans KLASS.
- Création d'école par le Super Admin
- Assistant de configuration initiale (Admin École)
"""
from django import forms
from django.core.validators import RegexValidator

from apps.core.utils import slugify_school_name
from .models import School


# ---------------------------------------------------------------------------
# Super Admin — Création d'une école
# ---------------------------------------------------------------------------

class CreateSchoolForm(forms.Form):
    """
    Formulaire de création d'une école par le Super Admin.
    Crée en une seule opération : l'école, le tenant PostgreSQL et l'Admin École.
    """
    # --- Informations de l'établissement ---
    name = forms.CharField(
        max_length=200,
        label="Nom de l'établissement",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "ex: École Saint-Joseph de Lubumbashi",
        }),
    )
    email = forms.EmailField(
        label="Email de contact de l'école",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "contact@ecole.cd",
        }),
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        label="Téléphone",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "+243 000 000 000",
        }),
    )
    address = forms.CharField(
        required=False,
        label="Adresse",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 2,
            "placeholder": "Adresse complète de l'établissement",
        }),
    )
    city = forms.CharField(
        max_length=100,
        required=False,
        label="Ville",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "ex: Lubumbashi",
        }),
    )
    country = forms.CharField(
        max_length=100,
        initial="Congo (RDC)",
        label="Pays",
        widget=forms.TextInput(attrs={
            "class": "form-control",
        }),
    )

    # --- Informations de l'Admin École ---
    admin_first_name = forms.CharField(
        max_length=100,
        label="Prénom de l'Admin École",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Prénom",
        }),
    )
    admin_last_name = forms.CharField(
        max_length=100,
        label="Nom de l'Admin École",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Nom de famille",
        }),
    )
    admin_email = forms.EmailField(
        label="Email de l'Admin École",
        help_text="Cet email sera utilisé comme identifiant de connexion de l'Admin École.",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "admin@ecole.cd",
        }),
    )

    def clean_name(self):
        name = self.cleaned_data["name"]
        slug = slugify_school_name(name)
        if not slug:
            raise forms.ValidationError("Le nom de l'école est invalide.")
        if School.objects.filter(slug=slug).exists():
            raise forms.ValidationError(
                f"Une école avec ce nom (code: {slug}) existe déjà. "
                "Veuillez choisir un nom différent."
            )
        return name

    def clean_admin_email(self):
        email = self.cleaned_data["admin_email"]
        from apps.accounts.models import User
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "Un utilisateur avec cet email existe déjà dans le système."
            )
        return email

    def clean(self):
        cleaned = super().clean()
        # Vérifier que l'email de contact et l'email admin sont différents
        # (pas obligatoire mais recommandé - pas de validation bloquante ici)
        return cleaned


# ---------------------------------------------------------------------------
# Assistant de configuration initiale — Admin École
# ---------------------------------------------------------------------------

class SchoolInfoSetupForm(forms.ModelForm):
    """
    Étape 1 de l'assistant : informations de l'école.
    Permet à l'Admin École de compléter/corriger les données de son établissement.
    """
    class Meta:
        model = School
        fields = ["name", "logo", "address", "city", "country", "email", "phone"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Nom officiel de l'établissement",
            }),
            "logo": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "image/*",
            }),
            "address": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Adresse complète de l'établissement",
            }),
            "city": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ville",
            }),
            "country": forms.TextInput(attrs={
                "class": "form-control",
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "contact@ecole.cd",
            }),
            "phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "+243 000 000 000",
            }),
        }
        labels = {
            "name": "Nom officiel de l'établissement",
            "logo": "Logo de l'école",
            "address": "Adresse",
            "city": "Ville",
            "country": "Pays",
            "email": "Email de contact",
            "phone": "Téléphone",
        }


class SchoolYearSetupForm(forms.Form):
    """
    Étape 2 de l'assistant : année scolaire initiale.
    Crée la première année scolaire active de l'établissement.
    """
    name = forms.CharField(
        max_length=20,
        label="Nom de l'année scolaire",
        help_text="Format recommandé : 2025-2026",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "ex: 2025-2026",
        }),
    )
    start_date = forms.DateField(
        label="Date de début",
        widget=forms.DateInput(attrs={
            "class": "form-control",
            "type": "date",
        }),
    )
    end_date = forms.DateField(
        label="Date de fin",
        widget=forms.DateInput(attrs={
            "class": "form-control",
            "type": "date",
        }),
    )

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and start >= end:
            raise forms.ValidationError(
                "La date de fin doit être postérieure à la date de début."
            )
        return cleaned
