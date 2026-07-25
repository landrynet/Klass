"""Formulaires de gestion des élèves, parents, matricules et inscriptions."""
from datetime import date

from django import forms
from django.db.models import Q

from apps.core.constants import EnrollmentStatus
from .models import MatriculeConfiguration, Parent, ParentStudent, Student, StudentEnrollment


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


# ---------------------------------------------------------------------------
# Phase 3.1 — Formulaires d'inscription
# ---------------------------------------------------------------------------

class EnrollmentForm(forms.Form):
    """Formulaire de création d'une inscription élève."""
    student = forms.ModelChoiceField(
        queryset=Student.objects.none(),
        label="Élève",
        empty_label="— Rechercher un élève —",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    school_year = forms.ModelChoiceField(
        queryset=None,  # défini dynamiquement
        label="Année scolaire",
        empty_label="— Sélectionner une année —",
        widget=forms.Select(attrs={"class": "form-select", "id": "id_school_year"}),
    )
    classroom = forms.ModelChoiceField(
        queryset=None,  # défini dynamiquement
        label="Classe",
        empty_label="— Sélectionner une classe —",
        widget=forms.Select(attrs={"class": "form-select", "id": "id_classroom"}),
    )
    status = forms.ChoiceField(
        choices=[
            (EnrollmentStatus.ACTIVE, "Active"),
            (EnrollmentStatus.PENDING, "En attente"),
        ],
        initial=EnrollmentStatus.ACTIVE,
        label="Statut initial",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    notes = forms.CharField(
        required=False,
        label="Notes",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )

    def __init__(self, *args, student_queryset=None, school_year_queryset=None, classroom_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if student_queryset is not None:
            self.fields["student"].queryset = student_queryset
        if school_year_queryset is not None:
            self.fields["school_year"].queryset = school_year_queryset
        if classroom_queryset is not None:
            self.fields["classroom"].queryset = classroom_queryset

    def clean(self):
        cleaned = super().clean()
        student = cleaned.get("student")
        school_year = cleaned.get("school_year")
        classroom = cleaned.get("classroom")
        status = cleaned.get("status")

        if student and school_year and status in EnrollmentStatus.ACTIVE_STATUSES:
            # Vérifier qu'il n'y a pas déjà une inscription active
            existing = StudentEnrollment.objects.filter(
                student=student,
                school_year=school_year,
                status__in=EnrollmentStatus.ACTIVE_STATUSES,
            )
            if existing.exists():
                existing_enrollment = existing.first()
                raise forms.ValidationError(
                    f"Cet élève est déjà inscrit dans la classe "
                    f"«\u00a0{existing_enrollment.classroom}\u00a0» pour cette année scolaire. "
                    f"Annulez l'inscription existante avant d'en créer une nouvelle."
                )

        if classroom and school_year:
            # Vérifier que la classe appartient à l'année scolaire
            if classroom.school_year_id != school_year.pk:
                raise forms.ValidationError(
                    "La classe sélectionnée n'appartient pas à l'année scolaire choisie."
                )

        if classroom and not classroom.is_active:
            self.add_error("classroom", "Cette classe est inactive et n'accepte plus d'inscriptions.")

        if classroom and classroom.is_archived:
            self.add_error("classroom", "Cette classe est archivée.")

        if school_year and school_year.is_archived:
            self.add_error("school_year", "Cette année scolaire est archivée, les inscriptions ne sont plus possibles.")

        return cleaned


class EnrollmentEditForm(forms.Form):
    """Formulaire de modification d'une inscription (statut + notes uniquement)."""
    status = forms.ChoiceField(
        choices=EnrollmentStatus.CHOICES,
        label="Statut",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    notes = forms.CharField(
        required=False,
        label="Notes",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )

    def clean_status(self):
        return self.cleaned_data["status"]


class ChangeClassForm(forms.Form):
    """
    Formulaire de changement de classe.
    Annule l'inscription courante et crée une nouvelle inscription dans la nouvelle classe.
    """
    new_classroom = forms.ModelChoiceField(
        queryset=None,
        label="Nouvelle classe",
        empty_label="— Sélectionner la nouvelle classe —",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    reason = forms.CharField(
        required=False,
        label="Motif du changement",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Ex: redoublement, transfert interne, capacité..."}),
    )

    def __init__(self, *args, classroom_queryset=None, current_classroom=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_classroom = current_classroom
        if classroom_queryset is not None:
            self.fields["new_classroom"].queryset = classroom_queryset

    def clean_new_classroom(self):
        classroom = self.cleaned_data.get("new_classroom")
        if classroom and self.current_classroom and classroom.pk == self.current_classroom.pk:
            raise forms.ValidationError("La nouvelle classe doit être différente de la classe actuelle.")
        if classroom and not classroom.is_active:
            raise forms.ValidationError("La classe sélectionnée est inactive.")
        if classroom and classroom.is_archived:
            raise forms.ValidationError("La classe sélectionnée est archivée.")
        return classroom


class EnrollmentStatusForm(forms.Form):
    """Formulaire rapide de changement de statut."""
    status = forms.ChoiceField(
        choices=EnrollmentStatus.CHOICES,
        label="Nouveau statut",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
