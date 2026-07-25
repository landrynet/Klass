# Multi-Tenant dans KLASS

## Principe

KLASS utilise **django-tenants** avec un schéma PostgreSQL dédié par école.

## Fonctionnement

1. La requête arrive sur `ecole-xyz.klass.app`
2. `TenantMainMiddleware` identifie le tenant depuis le sous-domaine
3. Django bascule automatiquement vers le schéma `school_ecole_xyz`
4. Toutes les requêtes DB suivantes lisent/écrivent dans ce schéma

## Flux de création d'une école

```
Super-Admin crée une école
        ↓
School.objects.create() → auto_create_schema = True
        ↓
PostgreSQL crée schema school_<slug>
        ↓
migrate_schemas applique les migrations sur le nouveau schéma
        ↓
Compte Admin école créé dans le schéma de l'école
        ↓
Identifiants temporaires générés (must_change_password=True)
```

## SHARED_APPS vs TENANT_APPS

| App | Schéma |
|-----|--------|
| django_tenants | public |
| apps.tenants (School, Domain) | public |
| apps.accounts (User) | public |
| django_celery_beat | public |
| apps.academics | tenant |
| apps.students | tenant |
| apps.finance | tenant |
| apps.scheduling | tenant |
| apps.resources | tenant |
| apps.school_years | tenant |
| apps.portal | tenant |
| apps.communications | tenant |
| apps.notifications | tenant |

## Isolation des données

- Impossible pour une école d'accéder aux données d'une autre (au niveau PostgreSQL)
- Le Super-Admin utilise `schema_context()` pour accéder aux données d'un tenant
- Les URLs sont préfixées par le sous-domaine (routage automatique)
