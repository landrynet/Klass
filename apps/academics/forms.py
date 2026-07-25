"""
Formulaires pour le module académique — Phase 2.0.
Niveaux et Options / Filières.
"""
from django import forms
from .models import Level, Option


class LevelForm(forms.Form):
    """
    Formulaire de création / modification d'un niveau scolaire.
    Le queryset school_year est injecté dans la vue (contexte tenant).
    """
    school_year = forms.ModelChoiceField(
        queryset=None,  # injecté dans la vue
        label="Année scolaire",
        empty_label="-- Sélectionner une année --",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    name = forms.CharField(
        max_length=100,
        label="Nom du niveau",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "ex: 1ère secondaire",
        }),
    )
    code = forms.CharField(
        max_length=10,
        required=False,
        label="Code (optionnel)",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "ex: 1SEC",
        }),
    )
    order = forms.IntegerField(
        min_value=0,
        initial=0,
        label="Ordre d'affichage",
        help_text="0 = premier, croissant. Permet de trier l'affichage des niveaux.",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        label="Niveau actif",
        help_text="Un niveau inactif ne peut pas être utilisé pour créer des classes.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def __init__(self, *args, school_year_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school_year_queryset is not None:
            self.fields["school_year"].queryset = school_year_queryset

    def clean_name(self):
        return self.cleaned_data["name"].strip()

    def clean_code(self):
        return self.cleaned_data.get("code", "").strip().upper()


class OptionForm(forms.Form):
    """
    Formulaire de création / modification d'une option / filière.
    Le queryset level est injecté dans la vue (contexte tenant).
    """
    level = forms.ModelChoiceField(
        queryset=None,  # injecté dans la vue
        label="Niveau",
        empty_label="-- Sélectionner un niveau --",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    name = forms.CharField(
        max_length=100,
        label="Nom de l'option",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "ex: Scientifique",
        }),
    )
    code = forms.CharField(
        max_length=10,
        required=False,
        label="Code (optionnel)",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "ex: SCI",
        }),
    )
    description = forms.CharField(
        required=False,
        label="Description (optionnel)",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": "Description de l'option ou filière...",
        }),
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        label="Option active",
        help_text="Une option inactive ne peut pas être utilisée pour créer des classes.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def __init__(self, *args, level_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if level_queryset is not None:
            self.fields["level"].queryset = level_queryset

    def clean_name(self):
        return self.cleaned_data["name"].strip()

    def clean_code(self):
        return self.cleaned_data.get("code", "").strip().upper()
