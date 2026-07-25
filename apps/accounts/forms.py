"""
Formulaires d'authentification pour KLASS.
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from .models import User


class LoginForm(AuthenticationForm):
    """Formulaire de connexion KLASS."""
    username = forms.EmailField(
        label="Adresse email",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "votre@email.com",
            "autofocus": True,
        })
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Mot de passe",
        })
    )

    error_messages = {
        "invalid_login": "Email ou mot de passe incorrect. Veuillez réessayer.",
        "inactive": "Ce compte est désactivé. Contactez l'administrateur.",
    }


class PasswordChangeFirstLoginForm(PasswordChangeForm):
    """Formulaire de changement de mot de passe obligatoire à la première connexion."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        self.fields["old_password"].label = "Mot de passe temporaire"
        self.fields["new_password1"].label = "Nouveau mot de passe"
        self.fields["new_password2"].label = "Confirmer le nouveau mot de passe"


class UserProfileForm(forms.ModelForm):
    """Formulaire de mise à jour du profil utilisateur."""
    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone", "photo"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
        }


class CreateUserForm(forms.ModelForm):
    """Formulaire de création d'utilisateur par l'Admin école."""
    password = forms.CharField(
        label="Mot de passe temporaire",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=False,
        help_text="Laissez vide pour générer automatiquement."
    )

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "role", "phone"]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "role": forms.Select(attrs={"class": "form-select"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
        }
