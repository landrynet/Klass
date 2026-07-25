# Base de données KLASS

## Configuration PostgreSQL

KLASS utilise PostgreSQL avec le backend multi-tenant de django-tenants.

### Variables d'environnement

```env
DATABASE_URL=postgres://klass:klass@localhost:5432/klass
```

### Configuration Django

```python
DATABASES = {
    "default": {
        **env.db("DATABASE_URL"),
        "ENGINE": "django_tenants.postgresql_backend",  # Obligatoire
    }
}
DATABASE_ROUTERS = ["django_tenants.routers.TenantSyncRouter"]
```

## Migrations

### Première installation

```bash
# Schéma public (tenants, accounts, celery beat)
python manage.py migrate_schemas --shared

# Schéma tenant (tous les modules métier)
python manage.py migrate_schemas
```

### Après modification de modèles

```bash
python manage.py makemigrations
python manage.py migrate_schemas --shared  # si app partagée
python manage.py migrate_schemas           # si app tenant
```

## Structure des schémas

### Schéma public

Contient les tables globales (écoles, domaines, utilisateurs super_admin).

### Schéma par école

Exemple: `school_ecole_xyz`

Contient toutes les données métier de l'école:
- `school_years_schoolyear`
- `academics_level`, `academics_option`, `academics_classroom`, `academics_room`, `academics_subject`
- `students_student`, `students_studentenrollment`, `students_parent`
- `teachers_teacher`, `teachers_teachersubject`
- `finance_feeconfig`, `finance_payment`, `finance_paymentreceipt`
- `scheduling_timeslot`, `scheduling_schedule`
- `resources_resource`, `resources_resourceaccess`
- `communications_message`
- `notifications_notification`
