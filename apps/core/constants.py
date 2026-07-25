"""
Constantes globales de KLASS.
"""

# ---------------------------------------------------------------------------
# Rôles utilisateurs
# ---------------------------------------------------------------------------
class Roles:
    SUPER_ADMIN = "super_admin"
    SCHOOL_ADMIN = "school_admin"
    SECRETARY = "secretary"
    ACCOUNTANT = "accountant"
    TEACHER = "teacher"
    PARENT = "parent"
    STUDENT = "student"

    CHOICES = [
        (SUPER_ADMIN, "Super Admin"),
        (SCHOOL_ADMIN, "Admin École"),
        (SECRETARY, "Secrétariat"),
        (ACCOUNTANT, "Comptable"),
        (TEACHER, "Enseignant"),
        (PARENT, "Parent"),
        (STUDENT, "Élève"),
    ]

    # Rôles avec accès au tableau de bord de gestion scolaire
    SCHOOL_STAFF_ROLES = [SCHOOL_ADMIN, SECRETARY, ACCOUNTANT, TEACHER]

    # Rôles avec accès au portail parents/élèves
    PORTAL_ROLES = [PARENT, STUDENT]

    # Rôles autorisés à modifier des données
    WRITE_ROLES = [SCHOOL_ADMIN, SECRETARY, ACCOUNTANT, TEACHER]

    @classmethod
    def all_values(cls):
        return [choice[0] for choice in cls.CHOICES]


# ---------------------------------------------------------------------------
# Statuts d'abonnement
# ---------------------------------------------------------------------------
class SubscriptionStatus:
    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"

    CHOICES = [
        (TRIAL, "Essai"),
        (ACTIVE, "Actif"),
        (SUSPENDED, "Suspendu"),
        (EXPIRED, "Expiré"),
    ]


# ---------------------------------------------------------------------------
# Genres
# ---------------------------------------------------------------------------
class Gender:
    MALE = "M"
    FEMALE = "F"

    CHOICES = [
        (MALE, "Masculin"),
        (FEMALE, "Féminin"),
    ]


# ---------------------------------------------------------------------------
# Types de paiement
# ---------------------------------------------------------------------------
class PaymentMethod:
    CASH = "cash"
    MOBILE_MONEY = "mobile_money"
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"

    CHOICES = [
        (CASH, "Espèces"),
        (MOBILE_MONEY, "Mobile Money"),
        (BANK_TRANSFER, "Virement bancaire"),
        (CHECK, "Chèque"),
    ]


# ---------------------------------------------------------------------------
# Types de frais scolaires
# ---------------------------------------------------------------------------
class FeeType:
    REGISTRATION = "registration"
    MONTHLY = "monthly"
    EXAM = "exam"
    TRANSPORT = "transport"
    OTHER = "other"

    CHOICES = [
        (REGISTRATION, "Frais d'inscription"),
        (MONTHLY, "Mensualité"),
        (EXAM, "Frais d'examen"),
        (TRANSPORT, "Transport"),
        (OTHER, "Autres frais"),
    ]


# ---------------------------------------------------------------------------
# Statuts d'inscription élève
# ---------------------------------------------------------------------------
class EnrollmentStatus:
    ACTIVE = "active"
    TRANSFERRED = "transferred"
    GRADUATED = "graduated"
    DROPPED = "dropped"
    REPEATING = "repeating"

    CHOICES = [
        (ACTIVE, "Actif"),
        (TRANSFERRED, "Transféré"),
        (GRADUATED, "Diplômé"),
        (DROPPED, "Abandonné"),
        (REPEATING, "Redoublant"),
    ]


# ---------------------------------------------------------------------------
# Types de ressources pédagogiques
# ---------------------------------------------------------------------------
class ResourceType:
    PDF = "pdf"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    LINK = "link"
    IMAGE = "image"

    CHOICES = [
        (PDF, "PDF"),
        (DOCUMENT, "Document"),
        (AUDIO, "Audio"),
        (VIDEO, "Vidéo"),
        (LINK, "Lien externe"),
        (IMAGE, "Image"),
    ]


# ---------------------------------------------------------------------------
# Jours de la semaine
# ---------------------------------------------------------------------------
class WeekDay:
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"

    CHOICES = [
        (MONDAY, "Lundi"),
        (TUESDAY, "Mardi"),
        (WEDNESDAY, "Mercredi"),
        (THURSDAY, "Jeudi"),
        (FRIDAY, "Vendredi"),
        (SATURDAY, "Samedi"),
    ]


# ---------------------------------------------------------------------------
# Types de messages
# ---------------------------------------------------------------------------
class MessageType:
    ANNOUNCEMENT = "announcement"
    ALERT = "alert"
    CONVOCATION = "convocation"
    PAYMENT_REMINDER = "payment_reminder"

    CHOICES = [
        (ANNOUNCEMENT, "Annonce"),
        (ALERT, "Alerte"),
        (CONVOCATION, "Convocation"),
        (PAYMENT_REMINDER, "Rappel de paiement"),
    ]
