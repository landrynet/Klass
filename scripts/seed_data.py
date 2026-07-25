#!/usr/bin/env python
"""
Script de données de démonstration pour KLASS — Phase 3.1.
Crée une école de test avec des données pour les Phases 1, 2.0, 2.1, 3.0 et 3.1.

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
from apps.core.constants import Roles, EnrollmentStatus
from apps.core.utils import generate_temp_password


def seed():
    """Créer les données de démonstration — Phases 1, 2.0, 2.1, 3.0 & 3.1."""
    print("=" * 60)
    print("KLASS — Données de démonstration [SEED] — Phase 3.1")
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

        year_2425, created = SchoolYear.objects.get_or_create(
            name="2024-2025 [SEED]",
            defaults={
                "start_date": datetime.date(2024, 9, 1),
                "end_date": datetime.date(2025, 6, 30),
                "is_active": False,
                "is_closed": True,
            }
        )
        print(f"   ✅ {year_2425.name} ({'créée' if created else 'existante'}) — {year_2425.status_display}")

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

        # Niveaux pour 2025-2026 (année active)
        niveaux_2526 = {}
        for nom, code, ordre in niveaux_data:
            level, created = Level.objects.get_or_create(
                school_year=year_2526,
                name=f"{nom} [SEED]",
                defaults={"code": code, "order": ordre, "is_active": True}
            )
            niveaux_2526[nom] = level
            if created:
                print(f"   ✅ {level.name} (créé)")

        # Niveaux pour 2024-2025 (historique)
        niveaux_2425 = {}
        for nom, code, ordre in niveaux_data:
            level, created = Level.objects.get_or_create(
                school_year=year_2425,
                name=f"{nom} [SEED]",
                defaults={"code": code, "order": ordre, "is_active": True}
            )
            niveaux_2425[nom] = level

        print(f"   ℹ️  {len(niveaux_2526)} niveaux vérifiés/créés (2025-2026)")

        # ---- 4. Options / Filières (Phase 2.0) ----
        print("\n4. Options / Filières...")
        options_data = [
            ("Scientifique", "SCI", "Sciences exactes et naturelles"),
            ("Littéraire", "LIT", "Lettres, philosophie et sciences humaines"),
            ("Commerciale", "COM", "Commerce, économie et gestion"),
        ]

        options_2526 = {}
        for nom_niveau, level in niveaux_2526.items():
            options_2526[nom_niveau] = {}
            for nom_opt, code_opt, desc in options_data:
                option, created = Option.objects.get_or_create(
                    level=level,
                    name=f"{nom_opt} [SEED]",
                    defaults={"code": code_opt, "description": desc, "is_active": True}
                )
                options_2526[nom_niveau][nom_opt] = option

        options_2425 = {}
        for nom_niveau, level in niveaux_2425.items():
            options_2425[nom_niveau] = {}
            for nom_opt, code_opt, desc in options_data:
                option, created = Option.objects.get_or_create(
                    level=level,
                    name=f"{nom_opt} [SEED]",
                    defaults={"code": code_opt, "description": desc, "is_active": True}
                )
                options_2425[nom_niveau][nom_opt] = option

        print(f"   ℹ️  Options créées/vérifiées pour toutes les années")

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
            if created:
                print(f"   ✅ {room.name} — {room.get_room_type_display()}, {room.capacity} places (créée)")
        print(f"   ℹ️  {len(rooms)} salles vérifiées")

        # ---- 6. Classes (Phase 2.1) ----
        print("\n6. Classes...")
        classes_data_2526 = [
            ("6ème secondaire", "Scientifique", "A", 40, "Salle 01 [SEED]"),
            ("6ème secondaire", "Scientifique", "B", 40, "Salle 02 [SEED]"),
            ("5ème secondaire", "Commerciale",  "A", 38, "Salle 01 [SEED]"),
            ("4ème secondaire", "Littéraire",   "A", 35, "Salle 02 [SEED]"),
            ("5ème secondaire", "Scientifique", "A", 40, "Salle 01 [SEED]"),
        ]

        classrooms_2526 = {}
        for nom_niveau, nom_option, section, capacite, nom_salle in classes_data_2526:
            level = niveaux_2526.get(nom_niveau)
            option = options_2526.get(nom_niveau, {}).get(nom_option)
            room = rooms.get(nom_salle)
            if not level or not option:
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
            classrooms_2526[f"{nom_niveau}_{nom_option}_{section}"] = classroom
            if created:
                print(f"   ✅ {classroom.full_name} — {classroom.capacity} élèves (créée)")

        # Classes pour 2024-2025 (historique)
        classrooms_2425 = {}
        classes_data_2425 = [
            ("5ème secondaire", "Scientifique", "A", 40, "Salle 01 [SEED]"),
            ("4ème secondaire", "Commerciale",  "A", 38, "Salle 02 [SEED]"),
        ]
        for nom_niveau, nom_option, section, capacite, nom_salle in classes_data_2425:
            level = niveaux_2425.get(nom_niveau)
            option = options_2425.get(nom_niveau, {}).get(nom_option)
            room = rooms.get(nom_salle)
            if not level or not option:
                continue
            classroom, created = Classroom.objects.get_or_create(
                school_year=year_2425,
                option=option,
                name=section,
                defaults={"capacity": capacite, "main_room": room, "is_active": True}
            )
            classrooms_2425[f"{nom_niveau}_{nom_option}_{section}"] = classroom

        print(f"   ℹ️  Classes 2025-2026 : {len(classrooms_2526)} | Classes 2024-2025 : {len(classrooms_2425)}")

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

        # ---- 9. Élèves de test (Phase 3.0) ----
        print("\n9. Élèves de test...")
        from apps.students.models import Parent, ParentStudent, Student, StudentEnrollment

        # Parent 1
        parent1, _ = Parent.objects.get_or_create(
            first_name="Marie",
            last_name="Mukendi [SEED]",
            defaults={
                "phone": "+243900000001",
                "email": "marie.mukendi.seed@example.com",
                "profession": "Commerçante",
            },
        )
        # Parent 2
        parent2, _ = Parent.objects.get_or_create(
            first_name="Paul",
            last_name="Kabongo [SEED]",
            defaults={
                "phone": "+243900000002",
                "email": "paul.kabongo.seed@example.com",
                "profession": "Enseignant",
            },
        )
        print(f"   ✅ Parents : {parent1}, {parent2}")

        # Élève 1 : Jean Kabila — a un historique sur 2 ans
        student1, created1 = Student.objects.get_or_create(
            first_name="Jean",
            last_name="Kabila [SEED]",
            defaults={
                "date_of_birth": datetime.date(2009, 3, 15),
                "gender": "M",
                "nationality": "Congolaise",
                "primary_parent": parent1,
            }
        )
        if student1.primary_parent_id != parent1.pk:
            student1.primary_parent = parent1
            student1.save(update_fields=["primary_parent", "updated_at"])
        ParentStudent.objects.get_or_create(parent=parent1, student=student1)
        print(f"   ✅ Élève 1 : {student1} — Matricule: {student1.matricule}")

        # Élève 2 : Claire Mutombo
        student2, created2 = Student.objects.get_or_create(
            first_name="Claire",
            last_name="Mutombo [SEED]",
            defaults={
                "date_of_birth": datetime.date(2010, 7, 22),
                "gender": "F",
                "nationality": "Congolaise",
                "primary_parent": parent2,
            }
        )
        if student2.primary_parent_id != parent2.pk:
            student2.primary_parent = parent2
            student2.save(update_fields=["primary_parent", "updated_at"])
        ParentStudent.objects.get_or_create(parent=parent2, student=student2)
        print(f"   ✅ Élève 2 : {student2} — Matricule: {student2.matricule}")

        # Élève 3 : Pierre Tshombe
        student3, created3 = Student.objects.get_or_create(
            first_name="Pierre",
            last_name="Tshombe [SEED]",
            defaults={
                "date_of_birth": datetime.date(2008, 11, 5),
                "gender": "M",
                "nationality": "Congolaise",
                "primary_parent": parent1,
            }
        )
        ParentStudent.objects.get_or_create(parent=parent1, student=student3)
        print(f"   ✅ Élève 3 : {student3} — Matricule: {student3.matricule}")

        # ---- 10. Inscriptions Phase 3.1 ----
        print("\n10. Inscriptions (Phase 3.1)...")

        cl_6sci_a = classrooms_2526.get("6ème secondaire_Scientifique_A")
        cl_6sci_b = classrooms_2526.get("6ème secondaire_Scientifique_B")
        cl_5sci_a = classrooms_2526.get("5ème secondaire_Scientifique_A")
        cl_5com_a = classrooms_2526.get("5ème secondaire_Commerciale_A")
        cl_5sci_2425 = classrooms_2425.get("5ème secondaire_Scientifique_A")

        # --- Élève 1 — Historique 2 ans ---
        # Inscription 2024-2025 (terminée)
        if cl_5sci_2425:
            enr1_hist, created = StudentEnrollment.objects.get_or_create(
                student=student1,
                school_year=year_2425,
                classroom=cl_5sci_2425,
                defaults={"status": EnrollmentStatus.COMPLETED, "notes": "Passé en 6ème"}
            )
            if created:
                print(f"   ✅ {student1.first_name} — 2024-2025 → {cl_5sci_2425.full_name} (Terminée) [créée]")
            else:
                print(f"   ℹ️  {student1.first_name} — 2024-2025 déjà existante")

        # Inscription 2025-2026 (active)
        if cl_6sci_a:
            enr1_active, created = StudentEnrollment.objects.get_or_create(
                student=student1,
                school_year=year_2526,
                classroom=cl_6sci_a,
                defaults={"status": EnrollmentStatus.ACTIVE}
            )
            if created:
                print(f"   ✅ {student1.first_name} — 2025-2026 → {cl_6sci_a.full_name} (Active) [créée]")
            else:
                print(f"   ℹ️  {student1.first_name} — 2025-2026 déjà existante ({enr1_active.get_status_display()})")

        # --- Élève 2 — Inscription active ---
        if cl_5sci_a:
            enr2, created = StudentEnrollment.objects.get_or_create(
                student=student2,
                school_year=year_2526,
                classroom=cl_5sci_a,
                defaults={"status": EnrollmentStatus.ACTIVE}
            )
            if created:
                print(f"   ✅ {student2.first_name} — 2025-2026 → {cl_5sci_a.full_name} (Active) [créée]")
            else:
                print(f"   ℹ️  {student2.first_name} — 2025-2026 déjà existante")

        # --- Élève 3 — Inscription en attente ---
        if cl_6sci_b:
            enr3, created = StudentEnrollment.objects.get_or_create(
                student=student3,
                school_year=year_2526,
                classroom=cl_6sci_b,
                defaults={"status": EnrollmentStatus.PENDING, "notes": "En attente de validation"}
            )
            if created:
                print(f"   ✅ {student3.first_name} — 2025-2026 → {cl_6sci_b.full_name} (En attente) [créée]")
            else:
                print(f"   ℹ️  {student3.first_name} — 2025-2026 déjà existante")

    print("\n" + "=" * 60)
    print("SEED TERMINÉ — Données Phase 3.1 créées/vérifiées")
    print("=" * 60)
    print(f"""
Récapitulatif :
  École    : {school.name}
  Schéma   : {school.schema_name}
  Années   : 2024-2025 (terminée), 2025-2026 (active), 2026-2027 (planifiée)
  Niveaux  : 6 niveaux par année
  Options  : 3 options par niveau
  Salles   : 5 salles
  Classes  : 5 classes 2025-2026, 2 classes 2024-2025
  Élèves   : 3 élèves de test
  Inscriptions :
    - Jean Kabila : 2024-2025 Terminée + 2025-2026 Active (historique)
    - Claire Mutombo : 2025-2026 Active
    - Pierre Tshombe : 2025-2026 En attente

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
