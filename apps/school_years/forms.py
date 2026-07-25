"""
Formulaires pour la gestion des années scolaires.
"""
from django import forms
from .models import SchoolYear


class SchoolYearForm(forms.Form):
    """
    Formulaire de création / modification d'une année scolaire.
    Utilisé à la fois pour créer et pour éditer (pas de ModelForm
    car la validation de l'unicité du nom doit être faite dans le
    service, dans le bon contexte tenant).
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
    activate = forms.BooleanField(
        required=False,
        label="Activer immédiatement",
        help_text="Si coché, cette année deviendra l'année active (la précédente sera désactivée).",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
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


class SchoolYearEditForm(forms.Form):
    """
    Formulaire de modification d'une année scolaire (sans le champ activate).
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
