# KLASS — Plateforme SaaS de Gestion Scolaire

## Overview
Multi-tenant school management platform built with Django 5.1 + django-tenants (one PostgreSQL schema per school), Bootstrap 5, HTMX, and Alpine.js. Developed for Université Don Bosco de Lubumbashi (UDBL).

## How to run
```bash
DJANGO_SETTINGS_MODULE=config.settings.development python manage.py runserver 0.0.0.0:5000
```
Or use the **Start application** workflow.

## Database
- **PostgreSQL** (Replit built-in, `DATABASE_URL` injected automatically)
- Migrations: `python manage.py migrate_schemas --shared && python manage.py migrate_schemas`

## Initial super admin account
- Email: `super@klass.app`
- Password: `SuperAdmin123!`

## Architecture
- `config/` — Django settings (base / development / production / testing)
- `apps/accounts/` — Custom User model (email login, roles, `school` FK)
- `apps/tenants/` — School/Domain models, create_school_with_tenant service, Super Admin views, Setup wizard
- `apps/core/` — Abstract models, constants, utils, middleware (TenantContext + SetupRequired)
- `apps/academics/` — Levels, options, classrooms, subjects, rooms
- `apps/school_years/` — SchoolYear model
- `apps/students/`, `apps/teachers/`, `apps/finance/`, `apps/scheduling/`, `apps/resources/`, `apps/portal/`, `apps/communications/`, `apps/notifications/`
- `templates/` — Django templates (Bootstrap 5)
- `docs/` — Project documentation

## Key URLs
- `/auth/login/` — Login page
- `/super-admin/` — Super Admin dashboard (school management)
- `/super-admin/schools/create/` — Create a new school
- `/super-admin/setup/school-info/` — Setup wizard step 1 (school admin)
- `/academics/` — School admin dashboard (after setup)

## User preferences
- Language: French (project is in French)
- No Django Admin — all management through custom interfaces
- Multi-tenant isolation: each school has its own PostgreSQL schema
- Celery runs in EAGER mode on Replit (no Redis required)
