"""Formulaires de gestion des élèves, parents et matricules."""
from datetime import date

from django import forms
from django.db.models import Q

from .models import MatriculeConfiguration, Parent, ParentStudent, Student


class ParentForm(forms.Form):
    first_name = forms.CharField(max_length=100, label="Prénom", widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(max_length=100, label="Nom", widget=forms.TextInput(attrs={"class": "form-control"}))
    gender = forms.ChoiceField(required=False, choices=[("", "— Non précisé —")] + list(Parent._meta.get_field("gender").choices), label="Genre", widget=forms.Select(attrs={"class": "form-select"}))
    phone = forms.CharField(max_length=20, label="Téléphone principal", widget=forms.TextInput(attrs={"class": "form-control"}))
    phone_secondary = forms.CharField(max_length=20, required=False, label="Téléphone secondaire", widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(required=False, label="Email", widget=forms.EmailInput(attrs={"class": "form-control"}))
    address = forms.CharField(required=False, label="Adresse", widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}))
    profession = forms.CharField(max_length=150, required=False, label="Profession", widget=forms.TextInput(attrs={"class": "form-control"}))

    def clean(self):
        cleaned = super().clean()
        for key in ("first_name", "last_name", "phone", "phone_secondary", "address", "profession"):
            if cleaned.get(key):
                cleaned[key] = cleaned[key].strip()
        return cleaned


class StudentForm(forms.Form):
    first_name = forms.CharField(max_length=100, label="Prénom", widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(max_length=100, label="Nom", widget=forms.TextInput(attrs={"class": "form-control"}))
    date_of_birth = forms.DateField(label="Date de naissance", widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))
    gender = forms.ChoiceField(choices=Student._meta.get_field("gender").choices, label="Genre", widget=forms.Select(attrs={"class": "form-select"}))
    primary_parent = forms.ModelChoiceField(queryset=Parent.objects.none(), label="Parent / tuteur principal", empty_label="— Sélectionner un parent —", widget=forms.Select(attrs={"class": "form-select"}))
    status = forms.ChoiceField(choices=Student._meta.get_field("status").choices, label="Statut", widget=forms.Select(attrs={"class": "form-select"}))

    def __init__(self, *args, parent_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if parent_queryset is not None:
            self.fields["primary_parent"].queryset = parent_queryset

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("date_of_birth") and cleaned["date_of_birth"] > date.today():
            self.add_error("date_of_birth", "La date de naissance ne peut pas être dans le futur.")
        for key in ("first_name", "last_name"):
            if cleaned.get(key):
                cleaned[key] = cleaned[key].strip()
        return cleaned


class MatriculeConfigurationForm(forms.Form):
    prefix = forms.CharField(max_length=10, label="Préfixe", widget=forms.TextInput(attrs={"class": "form-control", "style": "text-transform:uppercase"}))
    include_year = forms.BooleanField(required=False, label="Inclure l'année courante", widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))
    separator = forms.CharField(max_length=1, label="Séparateur", widget=forms.TextInput(attrs={"class": "form-control", "maxlength": "1"}))
    number_digits = forms.IntegerField(min_value=1, max_value=10, label="Nombre de chiffres", widget=forms.NumberInput(attrs={"class": "form-control"}))
    next_number = forms.IntegerField(min_value=1, label="Prochain numéro", widget=forms.NumberInput(attrs={"class": "form-control"}))

    def clean_prefix(self):
        return self.cleaned_data["prefix"].strip().upper()

    def clean_separator(self):
        return self.cleaned_data["separator"].strip() or "-"


def potential_parent_duplicates(data, exclude_pk=None):
    """Retourne les doublons évidents sans bloquer les homonymes."""
    qs = Parent.objects.filter(
        Q(phone=data.get("phone", "")) |
        (Q(email=data.get("email", "")) & ~Q(email="")) |
        Q(first_name__iexact=data.get("first_name", ""), last_name__iexact=data.get("last_name", ""))
    )
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    return qs.order_by("last_name", "first_name")