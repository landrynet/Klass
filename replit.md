# KLASS — Plateforme SaaS de Gestion Scolaire

## Overview
Multi-tenant school management platform built with Django 5.1 + django-tenants (one PostgreSQL schema per school), Bootstrap 5, HTMX, and Alpine.js. Developed for Université Don Bosco de Lubumbashi (UDBL).

## How to run
```bash
PORT=5000 ./run.sh --skip-git --skip-celery
```
Or use the **Start application** workflow.

## Database
- **PostgreSQL** (Replit built-in, `DATABASE_URL` injected automatically)
- Migrations: `python manage.py migrate_schemas --shared && python manage.py migrate_schemas`

## Initial super admin account
- Email: `super@klass.app`
- Password: `SuperAdmin123!`

## Seed data (development)
```bash
python scripts/seed_data.py
```
Creates a demo school with the academic structure, students, enrollments, and Phase 3.2 personnel/teachers (idempotent).

## Architecture
- `config/` — Django settings (base / development / production / testing)
- `apps/accounts/` — Custom User model (email login, roles, `school` FK)
- `apps/tenants/` — School/Domain models, create_school_with_tenant service, Super Admin views, Setup wizard
- `apps/core/` — Abstract models, constants, utils, middleware (TenantContext + SetupRequired)
- `apps/academics/` — Levels, options (CRUD Phase 2.0), classrooms, subjects, rooms (Phase 2.1)
- `apps/school_years/` — SchoolYear model + CRUD (Phase 2.0), 4-state lifecycle
- `apps/students/`, `apps/teachers/`, `apps/finance/`, `apps/scheduling/`, `apps/resources/`, `apps/portal/`, `apps/communications/`, `apps/notifications/`
- `templates/` — Django templates (Bootstrap 5)
- `docs/` — Project documentation

## Key URLs
- `/auth/login/` — Login page
- `/super-admin/` — Super Admin dashboard (school management)
- `/super-admin/schools/create/` — Create a new school
- `/super-admin/setup/school-info/` — Setup wizard step 1 (school admin)
- `/academics/` — School admin dashboard (after setup)
- `/school-years/` — School years management (Phase 2.0)
- `/academics/levels/` — Levels management (Phase 2.0)
- `/academics/options/` — Options/tracks management (Phase 2.0)

## Phase status
- **Phase 0** ✅ Multi-tenant foundation
- **Phase 1** ✅ School creation, setup wizard, school admin
- **Phase 2.0** ✅ School years CRUD, levels, options/tracks
- **Phase 2.1** ✅ Classrooms and rooms — CRUD, status lifecycle, tenant isolation
- **Phase 3.0** ✅ Students, parents, matricules
- **Phase 3.1** ✅ Enrollments — student → school year → classroom, history, class change
- **Phase 3.2** ✅ Personnel scolaire et enseignants — profils, statuts, matricules, recherche, filtres

## User preferences
- Language: French (project is in French)
- No Django Admin — all management through custom interfaces
- Multi-tenant isolation: each school has its own PostgreSQL schema
- Celery runs in EAGER mode on Replit (no Redis required)
- All tenant DB queries use explicit schema_context(school.schema_name)
