# Permissions et rôles KLASS

## Rôles

| Rôle | Code | Description |
|------|------|-------------|
| Super Admin | `super_admin` | Gère toute la plateforme (écoles, abonnements) |
| Admin École | `school_admin` | Directeur — accès complet à son école |
| Secrétariat | `secretary` | Gestion des inscriptions et dossiers élèves |
| Comptable | `accountant` | Paiements, reçus, rapports financiers |
| Enseignant | `teacher` | Emploi du temps + publication de ressources |
| Parent | `parent` | Portail en lecture (ses enfants) |
| Élève | `student` | Portail en lecture (ses propres données) |

## Décorateurs disponibles

```python
from apps.core.permissions import role_required, super_admin_required, school_staff_required

@role_required(Roles.SCHOOL_ADMIN, Roles.SECRETARY)
def ma_vue(request): ...

@super_admin_required
def admin_vue(request): ...

@school_staff_required
def staff_vue(request): ...
```

## Mixin pour Class-Based Views

```python
from apps.core.permissions import RolePermissionMixin
from apps.core.constants import Roles

class MaVue(RolePermissionMixin, View):
    allowed_roles = [Roles.SCHOOL_ADMIN, Roles.ACCOUNTANT]
```

## Accès par module

| Module | Super Admin | School Admin | Secretary | Accountant | Teacher | Parent | Student |
|--------|:-----------:|:------------:|:---------:|:----------:|:-------:|:------:|:-------:|
| Écoles | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Élèves | - | ✅ | ✅ | 👁 | 👁 | 👁* | 👁* |
| Paiements | - | ✅ | ❌ | ✅ | ❌ | 👁* | ❌ |
| Emploi du temps | - | ✅ | ❌ | ❌ | ✅ | 👁* | 👁* |
| Ressources | - | ✅ | ❌ | ❌ | ✅ | ❌ | 👁* |
| Portail | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |

✅ = accès complet, 👁 = lecture seule, 👁* = lecture seule via portail, ❌ = aucun accès
