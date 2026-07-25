"""
Formulaires pour le module académique — Phase 2.0 & 2.1.
Niveaux, Options / Filières, Classes, Salles.
"""
from django import forms
from .models import Level, Option, Classroom, Room


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


class ClassroomForm(forms.Form):
    """
    Formulaire de création / modification d'une classe.
    Les querysets option et main_room sont injectés dans la vue.
    """
    option = forms.ModelChoiceField(
        queryset=None,  # injecté dans la vue
        label="Option / Filière",
        empty_label="-- Sélectionner une option --",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    name = forms.CharField(
        max_length=50,
        label="Identifiant de la classe",
        help_text="Ex: A, B, C — différencie plusieurs classes du même niveau/option.",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "ex: A",
        }),
    )
    capacity = forms.IntegerField(
        min_value=1,
        initial=40,
        label="Capacité maximale (élèves)",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    main_room = forms.ModelChoiceField(
        queryset=None,  # injecté dans la vue
        required=False,
        label="Salle principale (optionnel)",
        empty_label="-- Aucune salle assignée --",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        label="Classe active",
        help_text="Une classe inactive n'accepte plus de nouvelles inscriptions.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def __init__(self, *args, option_queryset=None, room_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if option_queryset is not None:
            self.fields["option"].queryset = option_queryset
        if room_queryset is not None:
            self.fields["main_room"].queryset = room_queryset

    def clean_name(self):
        return self.cleaned_data["name"].strip()


class RoomForm(forms.Form):
    """
    Formulaire de création / modification d'une salle.
    """
    name = forms.CharField(
        max_length=100,
        label="Nom / Numéro de salle",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "ex: Salle 01, Laboratoire A",
        }),
    )
    code = forms.CharField(
        max_length=20,
        required=False,
        label="Code (optionnel)",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "ex: S01",
        }),
    )
    room_type = forms.ChoiceField(
        choices=Room.ROOM_TYPES,
        initial="classroom",
        label="Type de salle",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    capacity = forms.IntegerField(
        min_value=1,
        initial=40,
        label="Capacité (places)",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    floor = forms.CharField(
        max_length=20,
        required=False,
        label="Étage / Bâtiment (optionnel)",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "ex: RDC, Bâtiment A",
        }),
    )
    notes = forms.CharField(
        required=False,
        label="Notes (optionnel)",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 2,
            "placeholder": "Informations complémentaires...",
        }),
    )
    is_available = forms.BooleanField(
        required=False,
        initial=True,
        label="Salle disponible",
        help_text="Décochez si la salle est temporairement hors service.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def clean_name(self):
        return self.cleaned_data["name"].strip()

    def clean_code(self):
        return self.cleaned_data.get("code", "").strip().upper()
