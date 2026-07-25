"""
reset_test_data — Commande de gestion KLASS (dev uniquement)
=============================================================
Réinitialise les données de test dans le schéma tenant de démonstration.

Usage:
    python manage.py reset_test_data [--schema SCHEMA] [--yes] [--skip-confirm]

Cette commande :
  1. Vérifie que DEBUG=True (refuse d'exécuter en production)
  2. Demande confirmation interactive (sauf si --yes ou --skip-confirm)
  3. Purge toutes les données du schéma de démo
  4. Recrée un jeu de données complet :
     - 3 années scolaires (archived, ended, active)
     - 6 niveaux × 3 options = 18 filières
     - 20 classes réparties sur les niveaux
     - 8 salles
     - 50 élèves avec parents
     - 12 enseignants / 5 administratifs
     - ~60 inscriptions pour l'année active
"""
import random
from datetime import date, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django_tenants.utils import schema_context

# ---------------------------------------------------------------------------
# Données de test
# ---------------------------------------------------------------------------
FIRST_NAMES_M = [
    "Jean", "Pierre", "Paul", "Marc", "Luc", "David", "Emmanuel", "Samuel",
    "Joseph", "Daniel", "Nathan", "Caleb", "Benjamin", "Élie", "Josué",
    "Christophe", "Patrick", "Gérard", "Thierry", "Augustin",
]
FIRST_NAMES_F = [
    "Marie", "Sophie", "Claire", "Anne", "Julie", "Sarah", "Esther", "Ruth",
    "Naomi", "Rebecca", "Léa", "Rachel", "Deborah", "Mireille", "Claudette",
    "Joëlle", "Nadège", "Christelle", "Angélique", "Béatrice",
]
LAST_NAMES = [
    "Mutombo", "Kabila", "Nkosi", "Lumumba", "Kasongo", "Ngoy", "Mbuyi",
    "Tshimanga", "Kazadi", "Mulumba", "Banza", "Tshibanda", "Lukusa",
    "Ngalula", "Mwamba", "Ilunga", "Kalombo", "Mukendi", "Ngoie", "Kabongo",
    "Diallo", "Konaté", "Traoré", "Coulibaly", "Touré", "Dembélé", "Sanogo",
    "Kourouma", "Ouédraogo", "Sawadogo", "Compaoré", "Zongo",
]
SPECIALIZATIONS = [
    "Mathématiques", "Physique-Chimie", "Biologie", "Français",
    "Histoire-Géographie", "Informatique", "Économie", "Anglais",
    "Latin", "Éducation physique", "Philosophie", "Arts plastiques",
]
PHONE_PREFIXES = ["+243 8", "+243 9"]

LEVEL_DATA = [
    {"name": "1ère secondaire", "code": "S1", "order": 1},
    {"name": "2ème secondaire", "code": "S2", "order": 2},
    {"name": "3ème secondaire", "code": "S3", "order": 3},
    {"name": "4ème secondaire", "code": "S4", "order": 4},
    {"name": "5ème secondaire", "code": "S5", "order": 5},
    {"name": "6ème secondaire", "code": "S6", "order": 6},
]
OPTION_DATA = [
    {"name": "Sciences", "code": "SCI"},
    {"name": "Littéraire", "code": "LIT"},
    {"name": "Commercial", "code": "COM"},
]


def rng_name_m():
    return random.choice(FIRST_NAMES_M), random.choice(LAST_NAMES)


def rng_name_f():
    return random.choice(FIRST_NAMES_F), random.choice(LAST_NAMES)


def rng_phone():
    prefix = random.choice(PHONE_PREFIXES)
    return f"{prefix}{random.randint(10000000, 99999999)}"


def rng_dob():
    """Renvoie une date de naissance entre 10 et 20 ans."""
    today = date.today()
    age_days = random.randint(10 * 365, 20 * 365)
    return today - timedelta(days=age_days)


class Command(BaseCommand):
    help = "Réinitialise les données de test (dev only). Exige DEBUG=True."

    def add_arguments(self, parser):
        parser.add_argument(
            "--schema",
            default="ecole_demo",
            help="Nom du schéma tenant à réinitialiser (défaut: ecole_demo)",
        )
        parser.add_argument(
            "--yes", "-y",
            action="store_true",
            help="Ne pas demander de confirmation",
        )
        parser.add_argument(
            "--skip-confirm",
            action="store_true",
            help="Alias de --yes",
        )

    def handle(self, *args, **options):
        # ---- Garde : dev uniquement ----
        if not settings.DEBUG:
            raise CommandError(
                "⛔  Cette commande refuse de s'exécuter avec DEBUG=False. "
                "Elle est réservée à l'environnement de développement."
            )

        schema = options["schema"]
        skip = options["yes"] or options["skip_confirm"]

        self.stdout.write(self.style.WARNING(
            f"\n🗑️  Cette commande va SUPPRIMER et RECRÉER toutes les données du schéma «{schema}»."
        ))
        self.stdout.write("   Cela inclut : élèves, parents, inscriptions, enseignants, personnel, "
                          "salles, classes, options, niveaux et années scolaires.\n")

        if not skip:
            confirm = input("Tapez « CONFIRMER » pour continuer : ").strip()
            if confirm != "CONFIRMER":
                self.stdout.write(self.style.ERROR("Annulé."))
                return

        try:
            with schema_context(schema):
                self._reset(schema)
        except Exception as exc:
            raise CommandError(f"Erreur lors de la réinitialisation : {exc}") from exc

    # -----------------------------------------------------------------------
    def _reset(self, schema):
        from apps.students.models import Student, Parent, StudentParentLink, MatriculeConfig
        from apps.students.enrollments.models import StudentEnrollment
        from apps.academics.models import Level, Option, Classroom
        from apps.academics.rooms.models import Room
        from apps.academics.school_years.models import SchoolYear
        from apps.teachers.models import StaffMember

        self.stdout.write("  → Suppression des données existantes…")

        StudentEnrollment.objects.all().delete()
        StudentParentLink.objects.all().delete()
        Student.objects.all().delete()
        Parent.objects.all().delete()
        Classroom.objects.all().delete()
        Option.objects.all().delete()
        Level.objects.all().delete()
        SchoolYear.objects.all().delete()
        StaffMember.objects.all().delete()
        Room.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("  ✓ Données supprimées"))

        # ---- Années scolaires ----
        self.stdout.write("  → Création des années scolaires…")
        year_archived = SchoolYear.objects.create(
            name="2022-2023",
            start_date=date(2022, 9, 1),
            end_date=date(2023, 6, 30),
            is_active=False,
            is_closed=True,
            is_archived=True,
        )
        year_ended = SchoolYear.objects.create(
            name="2023-2024",
            start_date=date(2023, 9, 1),
            end_date=date(2024, 6, 30),
            is_active=False,
            is_closed=True,
            is_archived=False,
        )
        year_active = SchoolYear.objects.create(
            name="2024-2025",
            start_date=date(2024, 9, 1),
            end_date=date(2025, 6, 30),
            is_active=True,
            is_closed=False,
            is_archived=False,
        )
        self.stdout.write(self.style.SUCCESS(f"  ✓ 3 années scolaires créées"))

        # ---- Salles ----
        self.stdout.write("  → Création des salles…")
        rooms = []
        room_defs = [
            ("Salle A101", "A101", 45, "Bâtiment A"),
            ("Salle A102", "A102", 45, "Bâtiment A"),
            ("Salle B201", "B201", 50, "Bâtiment B"),
            ("Salle B202", "B202", 50, "Bâtiment B"),
            ("Salle B203", "B203", 40, "Bâtiment B"),
            ("Labo Sciences", "LAB-SCI", 30, "Bâtiment C"),
            ("Salle Informatique", "LAB-INFO", 25, "Bâtiment C"),
            ("Salle des fêtes", "SF-01", 200, "Bâtiment D"),
        ]
        for name, code, cap, building in room_defs:
            rooms.append(Room.objects.create(
                name=name, code=code, capacity=cap, building=building,
                is_available=True, is_archived=False,
            ))
        self.stdout.write(self.style.SUCCESS(f"  ✓ {len(rooms)} salles créées"))

        # ---- Niveaux & Options & Classes ----
        self.stdout.write("  → Création des niveaux, options et classes…")
        classrooms_by_option = {}
        all_classrooms = []
        for lyear in [year_active, year_ended]:
            for ld in LEVEL_DATA:
                level = Level.objects.create(
                    name=ld["name"],
                    code=ld["code"],
                    order=ld["order"],
                    is_active=True,
                    school_year=lyear,
                )
                for od in OPTION_DATA:
                    option = Option.objects.create(
                        name=od["name"],
                        code=od["code"],
                        level=level,
                        is_active=True,
                    )
                    # 1 classe par option pour year_ended, 2 pour year_active (S1/S2 only)
                    n_classes = 2 if (lyear == year_active and ld["order"] <= 2) else 1
                    for i in range(1, n_classes + 1):
                        suffix = chr(64 + i)  # A, B
                        cls_name = f"{ld['code']}/{od['code']}{suffix}" if n_classes > 1 else f"{ld['code']}/{od['code']}"
                        room = random.choice(rooms[:6])
                        classroom = Classroom.objects.create(
                            name=cls_name,
                            option=option,
                            room=room,
                            max_students=room.capacity or 40,
                            is_active=True,
                            is_archived=False,
                        )
                        all_classrooms.append(classroom)
                        if lyear == year_active:
                            classrooms_by_option.setdefault(option.pk, []).append(classroom)
        self.stdout.write(self.style.SUCCESS(f"  ✓ {len(all_classrooms)} classes créées"))

        # ---- Enseignants & Personnel ----
        self.stdout.write("  → Création du personnel (12 enseignants + 5 admin)…")
        for i in range(12):
            gender = "M" if i % 3 != 0 else "F"
            fn, ln = rng_name_m() if gender == "M" else rng_name_f()
            StaffMember.objects.create(
                first_name=fn, last_name=ln,
                gender=gender,
                staff_type="teacher",
                specialization=random.choice(SPECIALIZATIONS),
                contract_type=random.choice(["permanent", "temporary", "part_time"]),
                phone=rng_phone(),
                hire_date=date(2020, 9, 1) + timedelta(days=random.randint(0, 1200)),
                status="active",
            )
        for i in range(5):
            fn, ln = rng_name_f() if i % 2 == 0 else rng_name_m()
            types = ["administrative", "management", "technical", "other"]
            StaffMember.objects.create(
                first_name=fn, last_name=ln,
                gender="F" if i % 2 == 0 else "M",
                staff_type=types[i % len(types)],
                contract_type="permanent",
                phone=rng_phone(),
                hire_date=date(2019, 1, 1) + timedelta(days=random.randint(0, 1500)),
                status="active",
            )
        self.stdout.write(self.style.SUCCESS("  ✓ 17 membres du personnel créés"))

        # ---- MatriculeConfig ----
        MatriculeConfig.objects.update_or_create(
            defaults={
                "prefix": "EL",
                "year_format": "YY",
                "counter_digits": 4,
                "separator": "-",
            }
        )

        # ---- Élèves & Parents ----
        self.stdout.write("  → Création de 55 élèves avec parents…")
        parents_pool = []
        # Créer 30 parents
        for i in range(30):
            gender = "F" if i % 2 == 0 else "M"
            fn, ln = rng_name_f() if gender == "F" else rng_name_m()
            parent = Parent.objects.create(
                first_name=fn, last_name=ln,
                relationship_type=random.choice(["mother", "father", "guardian"]),
                phone=rng_phone(),
                email=f"{fn.lower()}.{ln.lower()}@demo.klass" if random.random() > 0.4 else "",
            )
            parents_pool.append(parent)

        students_list = []
        for i in range(55):
            gender = "M" if i % 3 != 2 else "F"
            fn, ln = rng_name_m() if gender == "M" else rng_name_f()
            primary_parent = random.choice(parents_pool)
            student = Student.objects.create(
                first_name=fn, last_name=ln,
                gender=gender,
                date_of_birth=rng_dob(),
                nationality="Congolaise",
                primary_parent=primary_parent,
                status="active",
            )
            # Lier un deuxième parent pour 30% des élèves
            if random.random() < 0.3:
                second_parent = random.choice(parents_pool)
                if second_parent.pk != primary_parent.pk:
                    StudentParentLink.objects.get_or_create(
                        student=student, parent=second_parent,
                        defaults={"relationship": "guardian", "is_primary": False},
                    )
            students_list.append(student)

        self.stdout.write(self.style.SUCCESS(f"  ✓ 55 élèves et 30 parents créés"))

        # ---- Inscriptions — année active ----
        self.stdout.write("  → Création des inscriptions pour l'année active…")
        active_classrooms = list(Classroom.objects.filter(
            option__level__school_year=year_active
        ).order_by("?"))

        if not active_classrooms:
            self.stdout.write(self.style.WARNING("  ⚠ Aucune classe active trouvée — inscriptions ignorées"))
        else:
            for idx, student in enumerate(students_list):
                classroom = active_classrooms[idx % len(active_classrooms)]
                enroll_date = year_active.start_date + timedelta(days=random.randint(0, 30))
                StudentEnrollment.objects.create(
                    student=student,
                    school_year=year_active,
                    classroom=classroom,
                    enrollment_date=enroll_date,
                    status="active",
                )

            # Quelques inscriptions supplémentaires pour l'année précédente
            for student in random.sample(students_list, min(30, len(students_list))):
                yr_cls = list(Classroom.objects.filter(option__level__school_year=year_ended).order_by("?"))
                if yr_cls:
                    classroom = random.choice(yr_cls)
                    StudentEnrollment.objects.get_or_create(
                        student=student,
                        school_year=year_ended,
                        defaults={
                            "classroom": classroom,
                            "enrollment_date": year_ended.start_date + timedelta(days=random.randint(0, 15)),
                            "status": "completed",
                        },
                    )
            self.stdout.write(self.style.SUCCESS(f"  ✓ 55+ inscriptions créées"))

        # ---- Résumé final ----
        self.stdout.write("\n" + "=" * 55)
        self.stdout.write(self.style.SUCCESS("✅  Données de test réinitialisées avec succès !\n"))
        self.stdout.write(f"   Schéma         : {schema}")
        self.stdout.write(f"   Années         : 3 (archived, ended, active)")
        self.stdout.write(f"   Niveaux        : {Level.objects.count()}")
        self.stdout.write(f"   Options        : {Option.objects.count()}")
        self.stdout.write(f"   Classes        : {Classroom.objects.count()}")
        self.stdout.write(f"   Salles         : {Room.objects.count()}")
        self.stdout.write(f"   Élèves         : {Student.objects.count()}")
        self.stdout.write(f"   Parents        : {Parent.objects.count()}")
        self.stdout.write(f"   Personnel      : {StaffMember.objects.count()}")
        self.stdout.write(f"   Inscriptions   : {StudentEnrollment.objects.count()}")
        self.stdout.write("=" * 55 + "\n")
