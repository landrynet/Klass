"""
Utilitaires communs pour KLASS.
"""
import uuid
import string
import random
from datetime import datetime


def generate_matricule(prefix: str = "KLS") -> str:
    """
    Génère un matricule unique pour un élève.
    Format: KLS-YYYY-XXXXXX (ex: KLS-2026-A3F7K2)
    """
    year = datetime.now().year
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{year}-{random_part}"


def generate_temp_password(length: int = 12) -> str:
    """
    Génère un mot de passe temporaire sécurisé.
    Utilisé lors de la création de comptes par le Super-Admin ou l'Admin école.
    """
    chars = string.ascii_letters + string.digits + "!@#$%"
    password = "".join(random.choices(chars, k=length))
    # S'assurer qu'il y a au moins un de chaque type
    password = (
        random.choice(string.ascii_uppercase)
        + random.choice(string.ascii_lowercase)
        + random.choice(string.digits)
        + random.choice("!@#$%")
        + "".join(random.choices(chars, k=length - 4))
    )
    return "".join(random.sample(password, len(password)))  # Mélanger


def generate_receipt_number(school_slug: str) -> str:
    """
    Génère un numéro de reçu unique.
    Format: SCHOOL-YYYY-UUID4 tronqué
    """
    year = datetime.now().year
    unique_part = uuid.uuid4().hex[:8].upper()
    return f"REC-{school_slug.upper()[:5]}-{year}-{unique_part}"


def slugify_school_name(name: str) -> str:
    """
    Crée un slug propre depuis le nom d'une école.
    Utilisé pour le sous-domaine et l'identifiant de schéma PostgreSQL.
    """
    import re
    slug = name.lower()
    slug = slug.replace(" ", "-")
    slug = re.sub(r"[àâä]", "a", slug)
    slug = re.sub(r"[éèêë]", "e", slug)
    slug = re.sub(r"[îï]", "i", slug)
    slug = re.sub(r"[ôö]", "o", slug)
    slug = re.sub(r"[ùûü]", "u", slug)
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:30]  # Maximum 30 caractères pour le sous-domaine
