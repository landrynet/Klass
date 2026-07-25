#!/usr/bin/env python
"""
Script de données de démonstration pour KLASS — Phase 2.1.
Crée une école de test avec des données pour les Phases 1, 2.0 et 2.1.

Usage:
    python scripts/seed_data.py

ATTENTION: Ne jamais exécuter en production !
Les données sont identifiées par le tag [SEED] pour faciliter la suppression.
Ce script est idempotent : exécutable plusieurs fois sans créer de doublons.
"""
import os
import sys
import datetime
import django

# Configurer Django avant d'importer quoi que ce soit
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.db import transaction
from apps.core.constants import Roles
from apps.core.utils import generate_temp_password


def seed():
    """Créer les données de démonstration — Phases 1, 2.0 & 2.1."""
    print("=" * 60)
    print("KLASS — Données de démonstration [SEED] — Phase 2.1")
    print("=" * 60)

    # ---- Vérifier l'environnement ----
    from django.conf import settings
    if not settings.DEBUG:
        print("ERREUR: Ce script ne peut être exécuté qu'en développement (DEBUG=True).")
        sys.exit(1)

    # ---- 1. Créer ou récupérer l'école de test ----
    print("\n1. École de démonstration...")
    try:
        from apps.tenants.services import create_school_with_tenant
        school, admin_user, _ = create_school_with_tenant(
            name="École Démo KLASS [SEED]",
            email="admin@demo-klass.app",
            phone="+243 000 000 000",
            address="123 Avenue de la Paix",
            city="Lubumbashi",
            country="Congo (RDC)",
            admin_first_name="Admin",
            admin_last_name="Démo",
            admin_email="admin@demo-klass.app",
        )
        print(f"   ✅ École créée : {school.name} (schéma: {school.schema_name})")
    except Exception as e:
        if "already exists" in str(e).lower() or "unique" in str(e).lower():
            print("   ℹ️  L'école de démonstration existe déjà — récupération")
            from apps.tenants.models import School
            school = School.objects.filter(slug__contains="demo-klass").first()
            if not school:
                print("   ❌ École introuvable après récupération.")
                return
            print(f"   ✅ École récupérée : {school.name}")
        else:
            print(f"   ❌ Erreur: {e}")
            raise

    # ---- Créer des données dans le schéma de l'école ----
    from django_tenants.utils import schema_context
    with schema_context(school.schema_name):

        # ---- 2. Années scolaires (Phase 2.0) ----
        print(f"\n2. Années scolaires dans le schéma {school.schema_name}...")
        from apps.school_years.models import SchoolYear

        year_2526, created = SchoolYear.objects.get_or_create(
            name="2025-2026 [SEED]",
            defaults={
                "start_date": datetime.date(2025, 9, 1),
                "end_date": datetime.date(2026, 6, 30),
                "is_active": True,
            }
        )
        print(f"   ✅ {year_2526.name} ({'créée' if created else 'existante'}) — {year_2526.status_display}")

        year_2627, created = SchoolYear.objects.get_or_create(
            name="2026-2027 [SEED]",
            defaults={
                "start_date": datetime.date(2026, 9, 1),
                "end_date": datetime.date(2027, 6, 30),
                "is_active": False,
            }
        )
        print(f"   ✅ {year_2627.name} ({'créée' if created else 'existante'}) — {year_2627.status_display}")

        # Garantir qu'une seule année est active
        if not SchoolYear.objects.filter(is_active=True).exists():
            year_2526.is_active = True
            year_2526.save(update_fields=["is_active"])
            print("   ℹ️  2025-2026 réactivée (aucune année active trouvée)")

        # ---- 3. Niveaux scolaires (Phase 2.0) ----
        print("\n3. Niveaux scolaires...")
        from apps.academics.models import Level, Option, Classroom, Room, Subject

        niveaux_data = [
            ("1ère secondaire", "1SEC", 0),
            ("2ème secondaire", "2SEC", 1),
            ("3ème secondaire", "3SEC", 2),
            ("4ème secondaire", "4SEC", 3),
            ("5ème secondaire", "5SEC", 4),
            ("6ème secondaire", "6SEC", 5),
        ]

        niveaux = {}
        for nom, code, ordre in niveaux_data:
            level, created = Level.objects.get_or_create(
                school_year=year_2526,
                name=f"{nom} [SEED]",
                defaults={"code": code, "order": ordre, "is_active": True}
            )
            niveaux[nom] = level
            print(f"   ✅ {level.name} ({'créé' if created else 'existant'})")

        # ---- 4. Options / Filières (Phase 2.0) ----
        print("\n4. Options / Filières...")
        options_data = [
            ("Scientifique", "SCI", "Sciences exactes et naturelles"),
            ("Littéraire", "LIT", "Lettres, philosophie et sciences humaines"),
            ("Commerciale", "COM", "Commerce, économie et gestion"),
        ]

        options_par_niveau = {}
        for nom_niveau, level in niveaux.items():
            options_par_niveau[nom_niveau] = {}
            for nom_opt, code_opt, desc in options_data:
                option, created = Option.objects.get_or_create(
                    level=level,
                    name=f"{nom_opt} [SEED]",
                    defaults={"code": code_opt, "description": desc, "is_active": True}
                )
                options_par_niveau[nom_niveau][nom_opt] = option
                if created:
                    print(f"   ✅ {option} (créée)")
        print(f"   ℹ️  {len(options_data) * len(niveaux)} options vérifiées/créées")

        # ---- 5. Salles (Phase 2.1) ----
        print("\n5. Salles...")
        rooms_data = [
            ("Salle 01 [SEED]",      "S01", "classroom",    50, "RDC"),
            ("Salle 02 [SEED]",      "S02", "classroom",    50, "RDC"),
            ("Laboratoire [SEED]",   "LAB", "laboratory",   30, "1er étage"),
            ("Salle Informatique [SEED]", "INFO", "computer_lab", 25, "1er étage"),
            ("Salle Polyvalente [SEED]",  "POLY", "polyvalent",   80, "RDC"),
        ]

        rooms = {}
        for name, code, rtype, cap, floor in rooms_data:
            room, created = Room.objects.get_or_create(
                name=name,
                defaults={
                    "code": code,
                    "room_type": rtype,
                    "capacity": cap,
                    "floor": floor,
                    "is_available": True,
                }
            )
            rooms[name] = room
            print(f"   ✅ {room.name} — {room.get_room_type_display()}, {room.capacity} places ({'créée' if created else 'existante'})")

        # ---- 6. Classes (Phase 2.1) ----
        print("\n6. Classes...")
        classes_data = [
            # (nom_niveau, nom_option, identifiant, capacité, nom_salle)
            ("6ème secondaire", "Scientifique", "A", 40, "Salle 01 [SEED]"),
            ("6ème secondaire", "Scientifique", "B", 40, "Salle 02 [SEED]"),
            ("5ème secondaire", "Commerciale",  "A", 38, "Salle 01 [SEED]"),
            ("4ème secondaire", "Littéraire",   "A", 35, "Salle 02 [SEED]"),
        ]

        for nom_niveau, nom_option, section, capacite, nom_salle in classes_data:
            level = niveaux.get(nom_niveau)
            option = options_par_niveau.get(nom_niveau, {}).get(nom_option)
            room = rooms.get(nom_salle)
            if not level or not option:
                print(f"   ⚠️  Niveau ou option introuvable pour {nom_niveau} / {nom_option}")
                continue
            classroom, created = Classroom.objects.get_or_create(
                school_year=year_2526,
                option=option,
                name=section,
                defaults={
                    "capacity": capacite,
                    "main_room": room,
                    "is_active": True,
                }
            )
            print(f"   ✅ {classroom.full_name} — {classroom.capacity} élèves ({'créée' if created else 'existante'})")

        # ---- 7. Matière ----
        subject, _ = Subject.objects.get_or_create(
            name="Mathématiques [SEED]",
            defaults={"code": "MATH"}
        )
        print(f"\n7. Matière : {subject}")

        # ---- 8. Utilisateurs de test ----
        print("\n8. Utilisateurs de test...")
        from apps.accounts.models import User
        test_users = [
            ("secretary@demo-klass.app", Roles.SECRETARY, "Secrétaire", "Démo"),
            ("accountant@demo-klass.app", Roles.ACCOUNTANT, "Comptable", "Démo"),
            ("teacher@demo-klass.app", Roles.TEACHER, "Enseignant", "Démo"),
            ("parent@demo-klass.app", Roles.PARENT, "Parent", "Démo"),
            ("student@demo-klass.app", Roles.STUDENT, "Élève", "Démo"),
        ]
        seed_password = os.environ.get("SEED_DEMO_PASSWORD")
        for email, role, first_name, last_name in test_users:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "role": role,
                    "school": school,
                }
            )
            if created:
                user.set_password(seed_password or generate_temp_password())
                user.save()
            print(f"   ✅ [{role}] {email} ({'créé' if created else 'existant'})")

        # ---- 9. Élève de test ----
        print("\n9. Élève de test...")
        from apps.students.models import Student, StudentEnrollment
        student, created = Student.objects.get_or_create(
            first_name="Jean",
            last_name="Kabila [SEED]",
            defaults={
                "date_of_birth": datetime.date(2010, 3, 15),
                "gender": "M",
                "nationality": "Congolaise",
            }
        )
        # Chercher la classe 6ème Scientifique A pour l'enrollment
        demo_classroom = Classroom.objects.filter(
            school_year=year_2526,
            option__name__contains="Scientifique",
            name="A"
        ).first()
        if created and demo_classroom:
            StudentEnrollment.objects.get_or_create(
                student=student,
                school_year=year_2526,
                defaults={"classroom": demo_classroom}
            )
        print(f"   ✅ Élève : {student} — Matricule: {student.matricule}")

    print("\n" + "=" * 60)
    print("SEED TERMINÉ — Données Phase 2.1 créées/vérifiées")
    print("=" * 60)
    print(f"""
Récapitulatif :
  École    : {school.name}
  Schéma   : {school.schema_name}
  Années   : 2025-2026 (active), 2026-2027 (planifiée)
  Niveaux  : 6 niveaux (1ère → 6ème secondaire)
  Options  : 3 options par niveau (Scientifique, Littéraire, Commerciale)
  Salles   : 5 salles (Salle 01, Salle 02, Labo, Info, Polyvalente)
  Classes  : 4 classes (6ème Sci A/B, 5ème Com A, 4ème Lit A)

⚠️  Ces données sont identifiées par le tag [SEED]
    Pour les supprimer, lancez: python scripts/seed_data.py --delete
""")


def delete_seed_data():
    """Suppression des données de démonstration [SEED]."""
    print("Suppression des données [SEED]...")
    from django.conf import settings
    if not settings.DEBUG:
        print("ERREUR: Uniquement en développement.")
        sys.exit(1)

    from apps.tenants.models import School
    seed_schools = School.objects.filter(name__contains="[SEED]")
    count = seed_schools.count()

    if count == 0:
        print("   ℹ️  Aucune donnée [SEED] trouvée.")
        return

    for school in seed_schools:
        print(f"   Suppression du tenant : {school.name} (schéma: {school.schema_name})")
        school.delete()  # supprime aussi le schéma via django-tenants

    # Supprimer les utilisateurs [SEED] restants dans le public schema
    from apps.accounts.models import User
    seed_users = User.objects.filter(email__contains="demo-klass")
    deleted_count = seed_users.count()
    seed_users.delete()

    print(f"   ✅ {count} école(s) et {deleted_count} utilisateur(s) supprimés.")


if __name__ == "__main__":
    if "--delete" in sys.argv:
        delete_seed_data()
    else:
        seed()
