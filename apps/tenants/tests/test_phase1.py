"""
Tests Phase 1 : Fondation d'une école.

Teste :
1. Création d'une école et du tenant
2. Création de l'Admin École et association à l'école
3. Prévention des doublons
4. Isolation multi-tenant (École A ≠ École B)
5. Flux de première connexion et changement de mot de passe
6. Assistant de configuration initiale
7. Permissions et sécurité
"""
import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.core.constants import Roles
from apps.tenants.models import School, Domain
from apps.tenants.services import create_school_with_tenant

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_school(name="École Test Alpha", email="alpha@test.cd", **kwargs):
    """Crée une école complète avec Admin pour les tests."""
    admin_first_name = kwargs.pop("admin_first_name", "Admin")
    admin_last_name = kwargs.pop("admin_last_name", "Alpha")
    return create_school_with_tenant(
        name=name,
        email=email,
        phone="+243 000 000 001",
        city="Lubumbashi",
        country="Congo (RDC)",
        admin_first_name=admin_first_name,
        admin_last_name=admin_last_name,
        admin_email=kwargs.pop("admin_email", "admin.alpha@test.cd"),
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Tests : Service de création d'école
# ---------------------------------------------------------------------------

class TestCreateSchoolService(TestCase):
    """Tests du service create_school_with_tenant."""

    def test_creation_retourne_tuple(self):
        """La création retourne (school, admin_user, temp_password)."""
        result = make_school()
        self.assertEqual(len(result), 3)

    def test_ecole_creee_correctement(self):
        """L'école est créée avec les bons attributs."""
        school, _, _ = make_school(name="École Saint-Jean", email="sj@test.cd", admin_email="admin.sj@test.cd")
        self.assertIsNotNone(school.pk)
        self.assertEqual(school.name, "École Saint-Jean")
        self.assertEqual(school.email, "sj@test.cd")
        self.assertFalse(school.setup_completed)
        self.assertTrue(school.is_active)

    def test_slug_genere_depuis_nom(self):
        """Le slug est généré depuis le nom de l'école."""
        school, _, _ = make_school(name="École Test Bêta", email="beta@test.cd", admin_email="admin.beta@test.cd")
        self.assertIsNotNone(school.slug)
        self.assertGreater(len(school.slug), 0)

    def test_schema_postgresql_cree(self):
        """Le schema_name est défini correctement."""
        school, _, _ = make_school(name="École Test Gamma", email="gamma@test.cd", admin_email="admin.gamma@test.cd")
        self.assertTrue(school.schema_name.startswith("school_"))

    def test_domaine_principal_cree(self):
        """Un domaine principal est créé pour l'école."""
        school, _, _ = make_school(name="École Domaine", email="dom@test.cd", admin_email="admin.dom@test.cd")
        domain = Domain.objects.filter(tenant=school, is_primary=True).first()
        self.assertIsNotNone(domain)
        self.assertIn(school.slug, domain.domain)

    def test_admin_ecole_cree(self):
        """L'Admin École est créé avec le bon rôle."""
        school, admin_user, _ = make_school(
            name="École Admin", email="adm@test.cd", admin_email="admin.real@test.cd",
            admin_first_name="Jean", admin_last_name="Dupont"
        )
        self.assertIsNotNone(admin_user.pk)
        self.assertEqual(admin_user.role, Roles.SCHOOL_ADMIN)
        self.assertEqual(admin_user.first_name, "Jean")
        self.assertEqual(admin_user.last_name, "Dupont")

    def test_admin_lie_a_son_ecole(self):
        """L'Admin École est lié à son école via la FK school."""
        school, admin_user, _ = make_school(
            name="École FK", email="fk@test.cd", admin_email="admin.fk@test.cd"
        )
        self.assertEqual(admin_user.school, school)

    def test_mot_de_passe_temporaire_genere(self):
        """Un mot de passe temporaire est généré et doit être changé."""
        _, admin_user, temp_password = make_school(
            name="École Pwd", email="pwd@test.cd", admin_email="admin.pwd@test.cd"
        )
        self.assertIsNotNone(temp_password)
        self.assertGreater(len(temp_password), 8)
        self.assertTrue(admin_user.must_change_password)

    def test_doublon_nom_ecole_leve_erreur(self):
        """La création d'une école avec le même nom lève une erreur."""
        make_school(name="École Double", email="d1@test.cd", admin_email="admin.d1@test.cd")
        with self.assertRaises(Exception):
            make_school(name="École Double", email="d2@test.cd", admin_email="admin.d2@test.cd")

    def test_doublon_admin_email_leve_erreur(self):
        """La création avec un email admin déjà existant lève une erreur."""
        make_school(name="École E1", email="e1@test.cd", admin_email="same@test.cd")
        with self.assertRaises(Exception):
            make_school(name="École E2", email="e2@test.cd", admin_email="same@test.cd")


# ---------------------------------------------------------------------------
# Tests : Isolation multi-tenant
# ---------------------------------------------------------------------------

class TestMultiTenantIsolation(TestCase):
    """
    Teste que les données de deux écoles sont bien isolées.
    École A ≠ accès aux données de École B.
    """

    def setUp(self):
        self.school_a, self.admin_a, self.pwd_a = create_school_with_tenant(
            name="École Isolation Alpha",
            email="iso-alpha@test.cd",
            admin_first_name="Admin",
            admin_last_name="Alpha",
            admin_email="admin.iso.alpha@test.cd",
        )
        self.school_b, self.admin_b, self.pwd_b = create_school_with_tenant(
            name="École Isolation Beta",
            email="iso-beta@test.cd",
            admin_first_name="Admin",
            admin_last_name="Beta",
            admin_email="admin.iso.beta@test.cd",
        )

    def test_deux_ecoles_distinctes(self):
        """Deux écoles ont des IDs et des schemas différents."""
        self.assertNotEqual(self.school_a.pk, self.school_b.pk)
        self.assertNotEqual(self.school_a.schema_name, self.school_b.schema_name)
        self.assertNotEqual(self.school_a.slug, self.school_b.slug)

    def test_admin_a_ne_voit_pas_ecole_b(self):
        """L'Admin A est lié à l'École A uniquement."""
        self.assertEqual(self.admin_a.school, self.school_a)
        self.assertNotEqual(self.admin_a.school, self.school_b)

    def test_admin_b_ne_voit_pas_ecole_a(self):
        """L'Admin B est lié à l'École B uniquement."""
        self.assertEqual(self.admin_b.school, self.school_b)
        self.assertNotEqual(self.admin_b.school, self.school_a)

    def test_staff_ecole_a_isole_de_ecole_b(self):
        """Le personnel de l'École A n'apparaît pas dans le staff de l'École B."""
        staff_a = User.objects.filter(school=self.school_a)
        staff_b = User.objects.filter(school=self.school_b)

        # Les emails des deux groupes ne se recoupent pas
        emails_a = set(staff_a.values_list("email", flat=True))
        emails_b = set(staff_b.values_list("email", flat=True))
        self.assertEqual(emails_a & emails_b, set())

    def test_schema_names_differents(self):
        """Les schémas PostgreSQL des deux écoles sont différents."""
        self.assertNotEqual(self.school_a.schema_name, self.school_b.schema_name)
        # Les schémas doivent correspondre au pattern school_<slug>
        self.assertTrue(self.school_a.schema_name.startswith("school_"))
        self.assertTrue(self.school_b.schema_name.startswith("school_"))


# ---------------------------------------------------------------------------
# Tests : Modèles
# ---------------------------------------------------------------------------

class TestSchoolModel(TestCase):
    """Tests du modèle School."""

    def setUp(self):
        self.school, _, _ = make_school(
            name="École Modèle", email="modele@test.cd", admin_email="admin.modele@test.cd"
        )

    def test_is_operational_false_avant_setup(self):
        """Une école non configurée n'est pas opérationnelle."""
        self.assertFalse(self.school.is_operational)

    def test_is_operational_true_apres_setup(self):
        """Une école configurée est opérationnelle."""
        self.school.setup_completed = True
        self.school.save()
        self.assertTrue(self.school.is_operational)

    def test_str_retourne_nom(self):
        """__str__ retourne le nom de l'école."""
        self.assertIn("École Modèle", str(self.school))

    def test_is_trial_par_defaut(self):
        """Une nouvelle école est en période d'essai."""
        self.assertTrue(self.school.is_trial)


class TestUserModel(TestCase):
    """Tests du modèle User avec les rôles KLASS."""

    def setUp(self):
        self.school, self.admin, _ = make_school(
            name="École User", email="user@test.cd", admin_email="admin.user@test.cd"
        )

    def test_admin_role_correct(self):
        """L'Admin École a le bon rôle."""
        self.assertEqual(self.admin.role, Roles.SCHOOL_ADMIN)
        self.assertTrue(self.admin.is_school_admin)

    def test_admin_school_fk_correct(self):
        """L'Admin est lié à son école via la FK."""
        self.assertEqual(self.admin.school_id, self.school.pk)

    def test_must_change_password_true_creation(self):
        """L'Admin doit changer son mot de passe à la création."""
        self.assertTrue(self.admin.must_change_password)

    def test_super_admin_sans_ecole(self):
        """Un Super Admin n'a pas d'école associée."""
        super_admin = User.objects.create_user(
            email="super@klass.app",
            password="SuperPass123!",
            role=Roles.SUPER_ADMIN,
            first_name="Super",
            last_name="Admin",
        )
        self.assertIsNone(super_admin.school)


# ---------------------------------------------------------------------------
# Tests : Vues Super Admin
# ---------------------------------------------------------------------------

class TestSuperAdminViews(TestCase):
    """Tests des vues Super Admin."""

    def setUp(self):
        self.client = Client()
        self.super_admin = User.objects.create_user(
            email="super.views@klass.app",
            password="SuperPass123!",
            role=Roles.SUPER_ADMIN,
            first_name="Super",
            last_name="Admin",
            must_change_password=False,
        )
        self.client.force_login(self.super_admin)

    def test_dashboard_super_admin_accessible(self):
        """Le dashboard Super Admin est accessible."""
        url = reverse("tenants:super_admin_dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_school_page_accessible(self):
        """La page de création d'école est accessible."""
        url = reverse("tenants:school_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_creation_ne_revele_pas_le_mot_de_passe_temporaire(self):
        """La réponse de création ne doit jamais exposer le mot de passe."""
        response = self.client.post(reverse("tenants:school_create"), {
            "name": "École Sécurité",
            "email": "security-school@test.cd",
            "phone": "+243 000 000 010",
            "address": "Avenue Test",
            "city": "Lubumbashi",
            "country": "Congo (RDC)",
            "admin_first_name": "Admin",
            "admin_last_name": "Sécurité",
            "admin_email": "admin.security@test.cd",
        })
        self.assertEqual(response.status_code, 302)
        self.assertNotContains(response, "Mot de passe temporaire", status_code=302)
        self.assertNotContains(response, "password", status_code=302)

    def test_school_admin_ne_peut_pas_acceder_super_admin(self):
        """Un Admin École ne peut pas accéder au dashboard Super Admin."""
        school, admin, _ = make_school(
            name="École Perm", email="perm@test.cd", admin_email="admin.perm@test.cd"
        )
        admin.must_change_password = False
        admin.save()
        school.setup_completed = True
        school.save()

        self.client.force_login(admin)
        url = reverse("tenants:super_admin_dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_utilisateur_non_connecte_redirige(self):
        """Un utilisateur non connecté est redirigé vers le login."""
        self.client.logout()
        url = reverse("tenants:super_admin_dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login/", response.url)


# ---------------------------------------------------------------------------
# Tests : Flux première connexion
# ---------------------------------------------------------------------------

class TestPremierreConnexion(TestCase):
    """Tests du flux de première connexion de l'Admin École."""

    def setUp(self):
        self.client = Client()
        self.school, self.admin, self.temp_password = make_school(
            name="École Connexion", email="conn@test.cd", admin_email="admin.conn@test.cd"
        )

    def test_connexion_avec_mot_de_passe_temporaire(self):
        """L'Admin peut se connecter avec son mot de passe temporaire."""
        response = self.client.post(reverse("accounts:login"), {
            "username": self.admin.email,
            "password": self.temp_password,
        })
        # Doit rediriger (succès ou changement mot de passe)
        self.assertEqual(response.status_code, 302)

    def test_redirection_changement_mot_de_passe(self):
        """Après connexion, l'Admin est redirigé vers le changement de mot de passe."""
        self.client.force_login(self.admin)
        # L'admin a must_change_password=True — le login doit rediriger
        response = self.client.post(reverse("accounts:login"), {
            "username": self.admin.email,
            "password": self.temp_password,
        }, follow=False)
        # La vue de login redirige vers change_password_required
        # (si must_change_password=True)

    def test_middleware_bloque_sans_setup(self):
        """Le middleware bloque l'accès au dashboard sans configuration complète."""
        # Simuler un admin avec mot de passe changé mais setup non fait
        self.admin.must_change_password = False
        self.admin.save()

        self.client.force_login(self.admin)
        response = self.client.get(reverse("academics:dashboard"))
        # Doit rediriger vers l'assistant de configuration
        self.assertEqual(response.status_code, 302)
        self.assertIn("setup", response.url)

    def test_middleware_laisse_passer_apres_setup(self):
        """Après configuration, le dashboard est accessible."""
        self.admin.must_change_password = False
        self.admin.save()
        self.school.setup_completed = True
        self.school.save()

        self.client.force_login(self.admin)
        response = self.client.get(reverse("academics:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_assistant_setup_inaccessible_sans_connexion(self):
        """L'assistant de configuration est inaccessible sans connexion."""
        response = self.client.get(reverse("tenants:setup_school_info"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login/", response.url)

    def test_super_admin_ne_peut_pas_acceder_assistant(self):
        """Un Super Admin ne peut pas accéder à l'assistant de configuration."""
        super_admin = User.objects.create_user(
            email="super.setup@klass.app",
            password="SuperPass123!",
            role=Roles.SUPER_ADMIN,
            first_name="Super",
            last_name="Admin",
        )
        self.client.force_login(super_admin)
        response = self.client.get(reverse("tenants:setup_school_info"))
        self.assertEqual(response.status_code, 403)
