"""
Vues d'authentification pour KLASS.
"""
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views import View
from .forms import LoginForm, PasswordChangeFirstLoginForm


def home_view(request):
    """
    Vue racine intelligente :
    - Utilisateur non connecté → page de connexion
    - super_admin → dashboard super-admin personnalisé
    - school_admin non configuré → assistant de configuration
    - Autres rôles → dashboard académique ou portail
    """
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    from apps.core.constants import Roles

    if request.user.role == Roles.SUPER_ADMIN:
        return redirect("tenants:super_admin_dashboard")

    if request.user.role in Roles.PORTAL_ROLES:
        return redirect("portal:dashboard")

    # School admin ou personnel scolaire
    if request.user.role == Roles.SCHOOL_ADMIN:
        school = getattr(request.user, "school", None)
        if school and not school.setup_completed:
            return redirect("tenants:setup_school_info")

    return redirect("academics:dashboard")


class LoginView(View):
    """Vue de connexion KLASS."""
    template_name = "accounts/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(self._get_redirect_url(request.user))
        form = LoginForm(request)
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # Enregistrer l'IP de connexion
            ip = request.META.get("REMOTE_ADDR")
            user.last_login_ip = ip
            user.save(update_fields=["last_login_ip"])
            login(request, user)
            messages.success(request, f"Bienvenue, {user.get_full_name()} !")

            # Vérifier si changement de mot de passe obligatoire (première connexion)
            if user.must_change_password:
                return redirect("accounts:change_password_required")

            return redirect(self._get_redirect_url(user))
        return render(request, self.template_name, {"form": form})

    def _get_redirect_url(self, user):
        from apps.core.constants import Roles
        if user.role == Roles.SUPER_ADMIN:
            return "/"  # home_view gère la redirection vers le dashboard super-admin
        elif user.role in Roles.PORTAL_ROLES:
            return "portal:dashboard"
        else:
            return "/"


@login_required
def logout_view(request):
    """Vue de déconnexion."""
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect("accounts:login")


@method_decorator(login_required, name="dispatch")
class ChangePasswordRequiredView(View):
    """Changement de mot de passe obligatoire à la première connexion."""
    template_name = "accounts/change_password_required.html"

    def get(self, request):
        if not request.user.must_change_password:
            return redirect("home")
        form = PasswordChangeFirstLoginForm(request.user)
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = PasswordChangeFirstLoginForm(request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            user.must_change_password = False
            user.save(update_fields=["must_change_password"])
            update_session_auth_hash(request, user)
            messages.success(request, "Mot de passe mis à jour avec succès.")

            # Si school_admin avec école non configurée → assistant de configuration
            from apps.core.constants import Roles
            if user.role == Roles.SCHOOL_ADMIN:
                school = getattr(user, "school", None)
                if school and not school.setup_completed:
                    messages.info(
                        request,
                        "Bienvenue ! Veuillez compléter la configuration de votre école."
                    )
                    return redirect("tenants:setup_school_info")

            return redirect("home")
        return render(request, self.template_name, {"form": form})
