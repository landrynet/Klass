#!/usr/bin/env python
"""
Script de données de démonstration pour KLASS.
Crée une école de test avec des données minimales pour le développement.

Usage:
    python scripts/seed_data.py

ATTENTION: Ne jamais exécuter en production !
Les données sont identifiées par le tag [SEED] pour faciliter la suppression.
"""
import os
import sys
import django

# Configurer Django avant d'importer quoi que ce soit
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.db import transaction
from apps.core.constants import Roles
from apps.core.utils import generate_temp_password


def seed():
    """Créer les données de démonstration."""
    print("=" * 60)
    print("KLASS — Création des données de démonstration [SEED]")
    print("=" * 60)

    # ---- Vérifier l'environnement ----
    from django.conf import settings
    if not settings.DEBUG:
        print("ERREUR: Ce script ne peut être exécuté qu'en développement (DEBUG=True).")
        sys.exit(1)

    # ---- Créer l'école de test ----
    print("\n1. Création de l'école de démonstration...")
    try:
        from apps.tenants.services import create_school_with_tenant
        school, admin_user, _ = create_school_with_tenant(
            name="École Démo KLASS [SEED]",
            email="admin@demo-klass.app",
            phone="+243 000 000 000",
            address="123 Avenue de la Paix",
            city="Lubumbashi",
            country="Congo (RDC)",
        )
        print(f"   ✅ École créée : {school.name}")
        print(f"   ✅ Schéma     : {school.schema_name}")
        print("   ✅ Compte Admin École créé")
        print("   ✅ Identifiants temporaires générés (non affichés)")

    except Exception as e:
        if "already exists" in str(e).lower() or "unique" in str(e).lower():
            print("   ℹ️  L'école de démonstration existe déjà — skipping")
            from apps.tenants.models import School
            school = School.objects.filter(slug__contains="demo-klass").first()
            if not school:
                print("   ERREUR: École introuvable.")
                return
        else:
            print(f"   ❌ Erreur: {e}")
            raise

    # ---- Créer des données dans le schéma de l'école ----
    from django_tenants.utils import schema_context
    with schema_context(school.schema_name):
        print(f"\n2. Création de données dans le schéma {school.schema_name}...")

        # Année scolaire
        from apps.school_years.models import SchoolYear
        import datetime
        school_year, created = SchoolYear.objects.get_or_create(
            name="2025-2026 [SEED]",
            defaults={
                "start_date": datetime.date(2025, 9, 1),
                "end_date": datetime.date(2026, 6, 30),
                "is_active": True,
            }
        )
        action = "créée" if created else "existante"
        print(f"   ✅ Année scolaire {action} : {school_year.name}")

        # Niveau
        from apps.academics.models import Level, Option, Classroom, Room, Subject
        level, _ = Level.objects.get_or_create(
            school_year=school_year,
            name="Terminale [SEED]",
            defaults={"code": "TERM", "order": 1}
        )

        # Option
        option, _ = Option.objects.get_or_create(
            level=level,
            name="Scientifique [SEED]",
            defaults={"code": "SCI"}
        )

        # Salle
        room, _ = Room.objects.get_or_create(
            name="Salle A101 [SEED]",
            defaults={"capacity": 40, "room_type": "classroom"}
        )

        # Classe
        classroom, _ = Classroom.objects.get_or_create(
            school_year=school_year,
            option=option,
            name="A",
            defaults={"capacity": 35, "main_room": room}
        )
        print(f"   ✅ Structure académique : {level} → {option} → Classe {classroom.name}")

        # Matière
        subject, _ = Subject.objects.get_or_create(
            name="Mathématiques [SEED]",
            defaults={"code": "MATH"}
        )
        print(f"   ✅ Matière créée : {subject}")

        # Utilisateurs de test (un par rôle)
        from apps.accounts.models import User
        test_users = [
            ("secretary@demo-klass.app", Roles.SECRETARY, "Secretaire", "Demo"),
            ("accountant@demo-klass.app", Roles.ACCOUNTANT, "Comptable", "Demo"),
            ("teacher@demo-klass.app", Roles.TEACHER, "Enseignant", "Demo"),
            ("parent@demo-klass.app", Roles.PARENT, "Parent", "Demo"),
            ("student@demo-klass.app", Roles.STUDENT, "Eleve", "Demo"),
        ]

        print("\n3. Création des utilisateurs de test...")
        seed_password = os.environ.get("SEED_DEMO_PASSWORD")
        for email, role, first_name, last_name in test_users:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "role": role,
                }
            )
            if created:
                user.set_password(seed_password or generate_temp_password())
                user.save()
            action = "créé" if created else "existant"
            print(f"   ✅ Compte de test [{role}] ({action}) — identifiants non affichés")

        # Élève de test
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
        if created:
            StudentEnrollment.objects.create(
                student=student,
                school_year=school_year,
                classroom=classroom,
            )
        print(f"\n   ✅ Élève de test : {student} — Matricule: {student.matricule}")

    print("\n" + "=" * 60)
    print("SEED TERMINÉ — Données de démonstration créées avec succès")
    print("=" * 60)
    print("\n⚠️  Ces données sont identifiées par le tag [SEED]")
    print("   Pour les supprimer, lancez: python scripts/seed_data.py --delete\n")


if __name__ == "__main__":
    if "--delete" in sys.argv:
        print("Suppression des données de démonstration [SEED]...")
        # Logique de suppression à implémenter selon les besoins
        print("TODO: Implémenter la suppression sélective [SEED]")
    else:
        seed()
