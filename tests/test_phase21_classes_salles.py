"""
Tests — Phase 2.1 : Classes et Salles.
Vérifie les modèles, formulaires et isolation tenant.
"""
from django.test import SimpleTestCase


# ---------------------------------------------------------------------------
# Tests du modèle Room
# ---------------------------------------------------------------------------

class TestRoomModel(SimpleTestCase):
    """Tests du modèle Room."""

    def test_room_has_is_available_field(self):
        """Room possède le champ is_available."""
        from apps.academics.models import Room
        field = Room._meta.get_field("is_available")
        self.assertTrue(field.default)

    def test_room_has_is_archived_field(self):
        """Room possède le champ is_archived (Phase 2.1)."""
        from apps.academics.models import Room
        field = Room._meta.get_field("is_archived")
        self.assertFalse(field.default)

    def test_room_has_code_field(self):
        """Room possède le champ code (Phase 2.1)."""
        from apps.academics.models import Room
        field = Room._meta.get_field("code")
        self.assertTrue(field.blank)

    def test_room_has_polyvalent_type(self):
        """Room inclut le type 'polyvalent'."""
        from apps.academics.models import Room
        types = dict(Room.ROOM_TYPES)
        self.assertIn("polyvalent", types)

    def test_room_ordering(self):
        """Les salles sont triées par nom."""
        from apps.academics.models import Room
        self.assertEqual(Room._meta.ordering, ["name"])

    def test_room_str_representation(self):
        """Le __str__ inclut nom, type et capacité."""
        from apps.academics.models import Room
        room = Room(name="Salle 01", room_type="classroom", capacity=40)
        s = str(room)
        self.assertIn("Salle 01", s)
        self.assertIn("40", s)

    def test_room_status_display_available(self):
        """Salle disponible → status_display = 'Disponible'."""
        from apps.academics.models import Room
        room = Room(is_available=True, is_archived=False)
        self.assertEqual(room.status_display, "Disponible")

    def test_room_status_display_unavailable(self):
        """Salle indisponible (non archivée) → 'Indisponible'."""
        from apps.academics.models import Room
        room = Room(is_available=False, is_archived=False)
        self.assertEqual(room.status_display, "Indisponible")

    def test_room_status_display_archived(self):
        """Salle archivée → 'Archivée'."""
        from apps.academics.models import Room
        room = Room(is_available=True, is_archived=True)
        self.assertEqual(room.status_display, "Archivée")

    def test_room_badge_class_available(self):
        """Salle disponible → badge vert."""
        from apps.academics.models import Room
        room = Room(is_available=True, is_archived=False)
        self.assertIn("success", room.status_badge_class)

    def test_room_badge_class_archived(self):
        """Salle archivée → badge rouge."""
        from apps.academics.models import Room
        room = Room(is_available=True, is_archived=True)
        self.assertIn("danger", room.status_badge_class)

    def test_room_is_tenant_aware(self):
        """Room hérite de TenantAwareModel."""
        from apps.academics.models import Room
        from apps.core.models import TenantAwareModel
        self.assertTrue(issubclass(Room, TenantAwareModel))


# ---------------------------------------------------------------------------
# Tests du modèle Classroom
# ---------------------------------------------------------------------------

class TestClassroomModel(SimpleTestCase):
    """Tests du modèle Classroom."""

    def test_classroom_has_is_active_field(self):
        """Classroom possède le champ is_active (Phase 2.1)."""
        from apps.academics.models import Classroom
        field = Classroom._meta.get_field("is_active")
        self.assertTrue(field.default)

    def test_classroom_has_is_archived_field(self):
        """Classroom possède le champ is_archived (Phase 2.1)."""
        from apps.academics.models import Classroom
        field = Classroom._meta.get_field("is_archived")
        self.assertFalse(field.default)

    def test_classroom_unique_together(self):
        """Une classe est unique par (school_year, option, name)."""
        from apps.academics.models import Classroom
        unique = [list(c) for c in Classroom._meta.unique_together]
        self.assertIn(["school_year", "option", "name"], unique)

    def test_classroom_ordering(self):
        """Les classes sont triées par année, ordre du niveau, nom."""
        from apps.academics.models import Classroom
        self.assertEqual(
            Classroom._meta.ordering,
            ["school_year", "option__level__order", "name"]
        )

    def test_classroom_status_display_active(self):
        """Classe active → status_display = 'Active'."""
        from apps.academics.models import Classroom
        c = Classroom(is_active=True, is_archived=False)
        self.assertEqual(c.status_display, "Active")

    def test_classroom_status_display_inactive(self):
        """Classe inactive (non archivée) → 'Inactive'."""
        from apps.academics.models import Classroom
        c = Classroom(is_active=False, is_archived=False)
        self.assertEqual(c.status_display, "Inactive")

    def test_classroom_status_display_archived(self):
        """Classe archivée → 'Archivée'."""
        from apps.academics.models import Classroom
        c = Classroom(is_active=False, is_archived=True)
        self.assertEqual(c.status_display, "Archivée")

    def test_classroom_badge_active(self):
        """Classe active → badge vert."""
        from apps.academics.models import Classroom
        c = Classroom(is_active=True, is_archived=False)
        self.assertIn("success", c.status_badge_class)

    def test_classroom_badge_inactive(self):
        """Classe inactive → badge secondaire."""
        from apps.academics.models import Classroom
        c = Classroom(is_active=False, is_archived=False)
        self.assertIn("secondary", c.status_badge_class)

    def test_classroom_badge_archived(self):
        """Classe archivée → badge danger."""
        from apps.academics.models import Classroom
        c = Classroom(is_active=False, is_archived=True)
        self.assertIn("danger", c.status_badge_class)

    def test_classroom_is_tenant_aware(self):
        """Classroom hérite de TenantAwareModel."""
        from apps.academics.models import Classroom
        from apps.core.models import TenantAwareModel
        self.assertTrue(issubclass(Classroom, TenantAwareModel))

    def test_classroom_has_main_room_fk(self):
        """Classroom possède une FK vers Room (optionnelle)."""
        from apps.academics.models import Classroom
        field = Classroom._meta.get_field("main_room")
        self.assertTrue(field.null)
        self.assertTrue(field.blank)


# ---------------------------------------------------------------------------
# Tests des formulaires Phase 2.1
# ---------------------------------------------------------------------------

class TestClassroomForm(SimpleTestCase):
    """Tests du formulaire ClassroomForm."""

    def test_classroom_form_fields_present(self):
        """ClassroomForm contient les champs attendus."""
        from apps.academics.forms import ClassroomForm
        form = ClassroomForm(option_queryset=None, room_queryset=None)
        for field in ["option", "name", "capacity", "main_room", "is_active"]:
            self.assertIn(field, form.fields)

    def test_classroom_form_name_stripped(self):
        """Le nom est trimé."""
        from apps.academics.forms import ClassroomForm
        form = ClassroomForm.__new__(ClassroomForm)
        form.cleaned_data = {"name": "  A  "}
        self.assertEqual(form.clean_name(), "A")

    def test_classroom_form_capacity_min(self):
        """La capacité minimale est 1."""
        from apps.academics.forms import ClassroomForm
        field = ClassroomForm(option_queryset=None, room_queryset=None).fields["capacity"]
        self.assertEqual(field.min_value, 1)


class TestRoomForm(SimpleTestCase):
    """Tests du formulaire RoomForm."""

    def test_room_form_fields_present(self):
        """RoomForm contient les champs attendus."""
        from apps.academics.forms import RoomForm
        form = RoomForm()
        for field in ["name", "code", "room_type", "capacity", "floor", "notes", "is_available"]:
            self.assertIn(field, form.fields)

    def test_room_form_code_cleaned_uppercase(self):
        """Le code est normalisé en majuscules."""
        from apps.academics.forms import RoomForm
        form = RoomForm.__new__(RoomForm)
        form.cleaned_data = {"code": "s01"}
        self.assertEqual(form.clean_code(), "S01")

    def test_room_form_name_stripped(self):
        """Le nom est trimé."""
        from apps.academics.forms import RoomForm
        form = RoomForm.__new__(RoomForm)
        form.cleaned_data = {"name": "  Salle 01  "}
        self.assertEqual(form.clean_name(), "Salle 01")


# ---------------------------------------------------------------------------
# Tests d'isolation tenant (configuration)
# ---------------------------------------------------------------------------

class TestPhase21TenantIsolation(SimpleTestCase):
    """Tests de configuration tenant pour Phase 2.1."""

    def test_classroom_model_is_tenant_aware(self):
        """Classroom est dans le schéma tenant."""
        from apps.academics.models import Classroom
        from apps.core.models import TenantAwareModel
        self.assertTrue(issubclass(Classroom, TenantAwareModel))

    def test_room_model_is_tenant_aware(self):
        """Room est dans le schéma tenant."""
        from apps.academics.models import Room
        from apps.core.models import TenantAwareModel
        self.assertTrue(issubclass(Room, TenantAwareModel))

    def test_academics_in_tenant_apps(self):
        """L'app academics est dans TENANT_APPS."""
        from config.tenant_config import TENANT_APPS
        self.assertIn("apps.academics", TENANT_APPS)

    def test_academics_not_in_shared_apps(self):
        """Les classes et salles ne sont pas dans SHARED_APPS."""
        from config.tenant_config import SHARED_APPS
        self.assertNotIn("apps.academics", SHARED_APPS)


# ---------------------------------------------------------------------------
# Tests de régression — Phase 2.0
# ---------------------------------------------------------------------------

class TestPhase20Regression(SimpleTestCase):
    """Tests de régression pour s'assurer que Phase 2.0 n'est pas cassée."""

    def test_level_model_unchanged(self):
        """Le modèle Level conserve ses champs Phase 2.0."""
        from apps.academics.models import Level
        for field_name in ["school_year", "name", "code", "order", "is_active"]:
            Level._meta.get_field(field_name)  # lève FieldDoesNotExist si absent

    def test_option_model_unchanged(self):
        """Le modèle Option conserve ses champs Phase 2.0."""
        from apps.academics.models import Option
        for field_name in ["level", "name", "code", "description", "is_active"]:
            Option._meta.get_field(field_name)

    def test_level_form_still_works(self):
        """LevelForm est toujours fonctionnel."""
        from apps.academics.forms import LevelForm
        form = LevelForm(school_year_queryset=None)
        self.assertIn("school_year", form.fields)

    def test_option_form_still_works(self):
        """OptionForm est toujours fonctionnel."""
        from apps.academics.forms import OptionForm
        form = OptionForm(level_queryset=None)
        self.assertIn("level", form.fields)

    def test_school_year_model_intact(self):
        """SchoolYear conserve ses champs Phase 2.0."""
        from apps.school_years.models import SchoolYear
        for field_name in ["name", "start_date", "end_date", "is_active", "is_archived"]:
            SchoolYear._meta.get_field(field_name)

    def test_classroom_fk_to_option(self):
        """Classroom est toujours liée à Option."""
        from apps.academics.models import Classroom, Option
        field = Classroom._meta.get_field("option")
        self.assertEqual(field.related_model, Option)

    def test_classroom_fk_to_school_year(self):
        """Classroom est toujours liée à SchoolYear."""
        from apps.academics.models import Classroom
        from apps.school_years.models import SchoolYear
        field = Classroom._meta.get_field("school_year")
        self.assertEqual(field.related_model, SchoolYear)


# ---------------------------------------------------------------------------
# Tests des URLs Phase 2.1
# ---------------------------------------------------------------------------

class TestPhase21URLs(SimpleTestCase):
    """Tests de résolution des URLs Phase 2.1."""

    def test_rooms_url_resolves(self):
        """L'URL /academics/rooms/ est correctement configurée."""
        from django.urls import reverse
        url = reverse("academics:rooms")
        self.assertEqual(url, "/academics/rooms/")

    def test_room_create_url_resolves(self):
        """L'URL de création de salle est correctement configurée."""
        from django.urls import reverse
        url = reverse("academics:room_create")
        self.assertEqual(url, "/academics/rooms/create/")

    def test_room_edit_url_resolves(self):
        """L'URL d'édition de salle accepte un pk."""
        from django.urls import reverse
        url = reverse("academics:room_edit", kwargs={"pk": 1})
        self.assertEqual(url, "/academics/rooms/1/edit/")

    def test_room_toggle_url_resolves(self):
        """L'URL de toggle de salle est correctement configurée."""
        from django.urls import reverse
        url = reverse("academics:room_toggle", kwargs={"pk": 1})
        self.assertEqual(url, "/academics/rooms/1/toggle/")

    def test_room_archive_url_resolves(self):
        """L'URL d'archivage de salle est correctement configurée."""
        from django.urls import reverse
        url = reverse("academics:room_archive", kwargs={"pk": 1})
        self.assertEqual(url, "/academics/rooms/1/archive/")

    def test_classrooms_url_resolves(self):
        """L'URL /academics/classrooms/ est correctement configurée."""
        from django.urls import reverse
        url = reverse("academics:classrooms")
        self.assertEqual(url, "/academics/classrooms/")

    def test_classroom_create_url_resolves(self):
        """L'URL de création de classe est correctement configurée."""
        from django.urls import reverse
        url = reverse("academics:classroom_create")
        self.assertEqual(url, "/academics/classrooms/create/")

    def test_classroom_edit_url_resolves(self):
        """L'URL d'édition de classe accepte un pk."""
        from django.urls import reverse
        url = reverse("academics:classroom_edit", kwargs={"pk": 1})
        self.assertEqual(url, "/academics/classrooms/1/edit/")

    def test_classroom_toggle_url_resolves(self):
        """L'URL de toggle de classe est correctement configurée."""
        from django.urls import reverse
        url = reverse("academics:classroom_toggle", kwargs={"pk": 1})
        self.assertEqual(url, "/academics/classrooms/1/toggle/")

    def test_classroom_archive_url_resolves(self):
        """L'URL d'archivage de classe est correctement configurée."""
        from django.urls import reverse
        url = reverse("academics:classroom_archive", kwargs={"pk": 1})
        self.assertEqual(url, "/academics/classrooms/1/archive/")
