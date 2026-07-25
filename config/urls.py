"""
Configuration des URLs principale de KLASS.
Chaque module possède son propre urls.py pour maintenir la modularité.
"""
from django.urls import path, include
from apps.accounts.views import home_view
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Racine auth-aware : redirige selon l'état de connexion et le rôle
    path("", home_view, name="home"),

    # Authentification
    path("auth/", include("apps.accounts.urls", namespace="accounts")),

    # Modules métier
    path("academics/", include("apps.academics.urls", namespace="academics")),
    path("school-years/", include("apps.school_years.urls", namespace="school_years")),
    path("students/", include("apps.students.urls", namespace="students")),
    path("teachers/", include("apps.teachers.urls", namespace="teachers")),
    path("finance/", include("apps.finance.urls", namespace="finance")),
    path("scheduling/", include("apps.scheduling.urls", namespace="scheduling")),
    path("resources/", include("apps.resources.urls", namespace="resources")),
    path("portal/", include("apps.portal.urls", namespace="portal")),
    path("communications/", include("apps.communications.urls", namespace="communications")),
]

# Fichiers media en développement uniquement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
