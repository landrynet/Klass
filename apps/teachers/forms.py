"""Formulaires de gestion du personnel et des enseignants (Phase 3.2)."""
from datetime import date

from django import forms

from apps.core.constants import Gender, StaffStatus, StaffType


class PersonnelForm(forms.Form):
    first_name = forms.CharField(max_length=100, label="Prénom", widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(max_length=100, label="Nom", widget=forms.TextInput(attrs={"class": "form-control"}))
    gender = forms.ChoiceField(
        required=False,
        choices=[("", "— Non précisé —")] + list(Gender.CHOICES),
        label="Genre",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    date_of_birth = forms.DateField(
        required=False,
        label="Date de naissance",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    phone = forms.CharField(required=False, max_length=20, label="Téléphone", widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(required=False, label="Email", widget=forms.EmailInput(attrs={"class": "form-control"}))
    address = forms.CharField(required=False, label="Adresse", widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}))
    staff_type = forms.ChoiceField(
        choices=StaffType.CHOICES, label="Type de personnel", widget=forms.Select(attrs={"class": "form-select"})
    )
    status = forms.ChoiceField(
        choices=StaffStatus.CHOICES, label="Statut", widget=forms.Select(attrs={"class": "form-select"})
    )
    specialization = forms.CharField(
        required=False, max_length=200, label="Spécialité", widget=forms.TextInput(attrs={"class": "form-control"})
    )
    education_level = forms.CharField(
        required=False, max_length=150, label="Niveau d'étude", widget=forms.TextInput(attrs={"class": "form-control"})
    )
    diploma = forms.CharField(
        required=False, max_length=200, label="Diplôme", widget=forms.TextInput(attrs={"class": "form-control"})
    )
    experience_years = forms.IntegerField(
        required=False, min_value=0, max_value=80, initial=0, label="Années d'expérience",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    hire_date = forms.DateField(
        required=False, label="Date d'embauche",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    contract_type = forms.ChoiceField(
        choices=[
            ("permanent", "Permanent"),
            ("temporary", "Temporaire"),
            ("volunteer", "Bénévole"),
        ],
        label="Type de contrat",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    notes = forms.CharField(
        required=False, label="Notes", widget=forms.Textarea(attrs={"class": "form-control", "rows": 3})
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("date_of_birth") and cleaned["date_of_birth"] > date.today():
            self.add_error("date_of_birth", "La date de naissance ne peut pas être dans le futur.")
        if cleaned.get("hire_date") and cleaned["hire_date"] > date.today():
            self.add_error("hire_date", "La date d'embauche ne peut pas être dans le futur.")
        for field in ("first_name", "last_name", "phone", "email", "address", "specialization", "education_level", "diploma", "notes"):
            if cleaned.get(field):
                cleaned[field] = cleaned[field].strip()
        return cleaned


class PersonnelStatusForm(forms.Form):
    status = forms.ChoiceField(
        choices=StaffStatus.CHOICES,
        label="Nouveau statut",
        widget=forms.Select(attrs={"class": "form-select"}),
    )