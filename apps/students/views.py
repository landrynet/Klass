"""Interfaces Phase 3.0 & 3.1 : élèves, parents, matricules, inscriptions."""
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
from django_tenants.utils import schema_context

from apps.core.constants import EnrollmentStatus, Roles
from .forms import (
    ChangeClassForm,
    EnrollmentEditForm,
    EnrollmentForm,
    EnrollmentStatusForm,
    MatriculeConfigurationForm,
    ParentForm,
    StudentForm,
    potential_parent_duplicates,
)
from .models import MatriculeConfiguration, Parent, ParentStudent, Student, StudentEnrollment


# ---------------------------------------------------------------------------
# Mixins de permission
# ---------------------------------------------------------------------------

class SchoolStaffMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if request.user.role not in Roles.SCHOOL_STAFF_ROLES:
            raise PermissionDenied("Accès réservé au personnel de l'école.")
        if not getattr(request.user, "school", None):
            raise PermissionDenied("Votre compte n'est associé à aucune école.")
        return super().dispatch(request, *args, **kwargs)


class SchoolAdminMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if request.user.role != Roles.SCHOOL_ADMIN:
            raise PermissionDenied("Accès réservé à l'Admin École.")
        if not getattr(request.user, "school", None):
            raise PermissionDenied("Votre compte n'est associé à aucune école.")
        return super().dispatch(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# Helpers internes
# ---------------------------------------------------------------------------

def cached_queryset(queryset):
    """Évalue un queryset dans schema_context et le conserve pour le template."""
    list(queryset)
    return queryset


def parent_queryset(school, query=""):
    with schema_context(school.schema_name):
        qs = Parent.objects.all()
        if query:
            qs = qs.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(phone__icontains=query) |
                Q(email__icontains=query)
            )
        return cached_queryset(qs.order_by("last_name", "first_name"))


# ---------------------------------------------------------------------------
# Phase 3.0 — Élèves
# ---------------------------------------------------------------------------

@method_decorator(login_required, name="dispatch")
class StudentListView(SchoolStaffMixin, View):
    template_name = "students/list.html"

    def get(self, request):
        school = request.user.school
        with schema_context(school.schema_name):
            qs = Student.objects.select_related("primary_parent")
            query = request.GET.get("q", "").strip()
            status = request.GET.get("status", "")
            if query:
                qs = qs.filter(
                    Q(matricule__icontains=query) |
                    Q(first_name__icontains=query) |
                    Q(last_name__icontains=query)
                )
            if status:
                qs = qs.filter(status=status)
            students = list(qs.order_by("last_name", "first_name"))
        return render(request, self.template_name, {
            "students": students, "q": query, "status": status, "school": school,
        })


@method_decorator(login_required, name="dispatch")
class StudentCreateView(SchoolAdminMixin, View):
    template_name = "students/form.html"

    def get(self, request):
        school = request.user.school
        parents = parent_queryset(school, request.GET.get("parent_q", "").strip())
        form = StudentForm(parent_queryset=parents, initial={"status": "active"})
        return render(request, self.template_name, {
            "form": form, "title": "Nouvel élève",
            "parent_q": request.GET.get("parent_q", ""), "school": school,
        })

    def post(self, request):
        school = request.user.school
        parents = parent_queryset(school, request.POST.get("parent_q", "").strip())
        form = StudentForm(request.POST, parent_queryset=parents)
        if form.is_valid():
            data = form.cleaned_data
            with schema_context(school.schema_name), transaction.atomic():
                student = Student.objects.create(**data)
                ParentStudent.objects.get_or_create(parent=data["primary_parent"], student=student)
            messages.success(request, f"Élève créé avec le matricule {student.matricule}.")
            return redirect("students:detail", pk=student.pk)
        return render(request, self.template_name, {
            "form": form, "title": "Nouvel élève",
            "parent_q": request.POST.get("parent_q", ""), "school": school,
        })


@method_decorator(login_required, name="dispatch")
class StudentDetailView(SchoolStaffMixin, View):
    def get(self, request, pk):
        school = request.user.school
        with schema_context(school.schema_name):
            student = get_object_or_404(Student.objects.select_related("primary_parent"), pk=pk)
            links = list(student.parent_links.select_related("parent").all())
            enrollments = list(
                student.enrollments
                .select_related("school_year", "classroom", "classroom__option", "classroom__option__level")
                .order_by("-school_year__start_date", "-enrollment_date")
            )
            # Inscription active courante
            current_enrollment = next(
                (e for e in enrollments if e.status in EnrollmentStatus.ACTIVE_STATUSES), None
            )
        return render(request, "students/detail.html", {
            "student": student,
            "parent_links": links,
            "enrollments": enrollments,
            "current_enrollment": current_enrollment,
            "EnrollmentStatus": EnrollmentStatus,
            "school": school,
        })


@method_decorator(login_required, name="dispatch")
class StudentEditView(SchoolAdminMixin, View):
    template_name = "students/form.html"

    def get(self, request, pk):
        school = request.user.school
        with schema_context(school.schema_name):
            student = get_object_or_404(Student, pk=pk)
            parents = parent_queryset(school)
            form = StudentForm(parent_queryset=parents, initial={
                "first_name": student.first_name, "last_name": student.last_name,
                "date_of_birth": student.date_of_birth, "gender": student.gender,
                "primary_parent": student.primary_parent, "status": student.status,
            })
        return render(request, self.template_name, {
            "form": form, "title": "Modifier l'élève", "student": student, "school": school,
        })

    def post(self, request, pk):
        school = request.user.school
        with schema_context(school.schema_name):
            student = get_object_or_404(Student, pk=pk)
            parents = parent_queryset(school)
            form = StudentForm(request.POST, parent_queryset=parents)
            if form.is_valid():
                data = form.cleaned_data
                for field, value in data.items():
                    setattr(student, field, value)
                student.save(update_fields=["first_name", "last_name", "date_of_birth", "gender", "primary_parent", "status", "updated_at"])
                ParentStudent.objects.get_or_create(parent=data["primary_parent"], student=student)
                messages.success(request, "Élève mis à jour.")
                return redirect("students:detail", pk=student.pk)
        return render(request, self.template_name, {
            "form": form, "title": "Modifier l'élève", "student": student, "school": school,
        })


# ---------------------------------------------------------------------------
# Phase 3.0 — Parents
# ---------------------------------------------------------------------------

@method_decorator(login_required, name="dispatch")
class ParentListView(SchoolStaffMixin, View):
    def get(self, request):
        school = request.user.school
        with schema_context(school.schema_name):
            query = request.GET.get("q", "").strip()
            qs = Parent.objects.annotate(student_count=Count("students"))
            if query:
                qs = qs.filter(
                    Q(first_name__icontains=query) |
                    Q(last_name__icontains=query) |
                    Q(phone__icontains=query) |
                    Q(email__icontains=query)
                )
            parents = list(qs.order_by("last_name", "first_name"))
        return render(request, "students/parents_list.html", {
            "parents": parents, "q": query, "school": school,
        })


@method_decorator(login_required, name="dispatch")
class ParentCreateView(SchoolAdminMixin, View):
    template_name = "students/parent_form.html"

    def get(self, request):
        return render(request, self.template_name, {
            "form": ParentForm(), "title": "Nouveau parent / tuteur", "school": request.user.school,
        })

    def post(self, request):
        school = request.user.school
        form = ParentForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            with schema_context(school.schema_name):
                duplicates = list(potential_parent_duplicates(data))
                if duplicates and request.POST.get("confirm_duplicate") != "1":
                    return render(request, self.template_name, {
                        "form": form, "duplicates": duplicates,
                        "title": "Nouveau parent / tuteur", "school": school,
                    })
                parent = Parent.objects.create(**data)
            messages.success(request, "Parent / tuteur créé.")
            return redirect("students:parent_detail", pk=parent.pk)
        return render(request, self.template_name, {
            "form": form, "title": "Nouveau parent / tuteur", "school": school,
        })


@method_decorator(login_required, name="dispatch")
class ParentDetailView(SchoolStaffMixin, View):
    def get(self, request, pk):
        school = request.user.school
        with schema_context(school.schema_name):
            parent = get_object_or_404(Parent, pk=pk)
            students = list(parent.students.all().order_by("last_name", "first_name"))
        return render(request, "students/parent_detail.html", {
            "parent": parent, "students": students, "school": school,
        })


@method_decorator(login_required, name="dispatch")
class ParentEditView(SchoolAdminMixin, View):
    template_name = "students/parent_form.html"

    def get(self, request, pk):
        school = request.user.school
        with schema_context(school.schema_name):
            parent = get_object_or_404(Parent, pk=pk)
            form = ParentForm(initial={
                field: getattr(parent, field)
                for field in ("first_name", "last_name", "gender", "phone", "phone_secondary", "email", "address", "profession")
            })
        return render(request, self.template_name, {
            "form": form, "title": "Modifier le parent / tuteur", "parent": parent, "school": school,
        })

    def post(self, request, pk):
        school = request.user.school
        with schema_context(school.schema_name):
            parent = get_object_or_404(Parent, pk=pk)
            form = ParentForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                duplicates = list(potential_parent_duplicates(data, exclude_pk=pk))
                if duplicates and request.POST.get("confirm_duplicate") != "1":
                    return render(request, self.template_name, {
                        "form": form, "duplicates": duplicates,
                        "title": "Modifier le parent / tuteur", "parent": parent, "school": school,
                    })
                for field, value in data.items():
                    setattr(parent, field, value)
                parent.save()
                messages.success(request, "Parent / tuteur mis à jour.")
                return redirect("students:parent_detail", pk=parent.pk)
        return render(request, self.template_name, {
            "form": form, "title": "Modifier le parent / tuteur", "parent": parent, "school": school,
        })


# ---------------------------------------------------------------------------
# Phase 3.0 — Configuration des matricules
# ---------------------------------------------------------------------------

@method_decorator(login_required, name="dispatch")
class MatriculeConfigurationView(SchoolAdminMixin, View):
    template_name = "students/matricule_config.html"

    def get(self, request):
        school = request.user.school
        with schema_context(school.schema_name):
            config, _ = MatriculeConfiguration.objects.get_or_create(pk=1)
            form = MatriculeConfigurationForm(initial={
                field: getattr(config, field)
                for field in ("prefix", "include_year", "separator", "number_digits", "next_number")
            })
            preview = config.preview()
        return render(request, self.template_name, {
            "form": form, "preview": preview, "school": school,
        })

    def post(self, request):
        school = request.user.school
        with schema_context(school.schema_name):
            config, _ = MatriculeConfiguration.objects.get_or_create(pk=1)
            form = MatriculeConfigurationForm(request.POST)
            if form.is_valid():
                for field, value in form.cleaned_data.items():
                    setattr(config, field, value)
                config.save()
                messages.success(request, "Configuration des matricules enregistrée.")
                return redirect("students:matricule_config")
            preview = config.preview()
        return render(request, self.template_name, {
            "form": form, "preview": preview, "school": school,
        })


# ---------------------------------------------------------------------------
# Phase 3.1 — Inscriptions (Enrollments)
# ---------------------------------------------------------------------------

def _get_school_years(school):
    """Retourne les années scolaires non-archivées de l'école."""
    from apps.school_years.models import SchoolYear
    with schema_context(school.schema_name):
        return list(SchoolYear.objects.filter(is_archived=False).order_by("-start_date"))


def _get_classrooms_for_year(school, school_year_pk):
    """Retourne les classes actives pour une année donnée."""
    from apps.academics.models import Classroom
    with schema_context(school.schema_name):
        return list(
            Classroom.objects.filter(
                school_year_id=school_year_pk,
                is_active=True,
                is_archived=False,
            ).select_related("option", "option__level").order_by(
                "option__level__order", "option__name", "name"
            )
        )


@method_decorator(login_required, name="dispatch")
class EnrollmentListView(SchoolStaffMixin, View):
    """Liste de toutes les inscriptions avec recherche et filtres."""
    template_name = "students/enrollments/list.html"

    def get(self, request):
        school = request.user.school
        from apps.school_years.models import SchoolYear
        from apps.academics.models import Classroom

        with schema_context(school.schema_name):
            qs = StudentEnrollment.objects.select_related(
                "student", "school_year", "classroom",
                "classroom__option", "classroom__option__level",
            )

            # Filtres
            query = request.GET.get("q", "").strip()
            year_id = request.GET.get("year", "").strip()
            status_filter = request.GET.get("status", "").strip()
            classroom_id = request.GET.get("classroom", "").strip()

            if query:
                qs = qs.filter(
                    Q(student__matricule__icontains=query) |
                    Q(student__first_name__icontains=query) |
                    Q(student__last_name__icontains=query)
                )
            if year_id:
                qs = qs.filter(school_year_id=year_id)
            if status_filter:
                qs = qs.filter(status=status_filter)
            if classroom_id:
                qs = qs.filter(classroom_id=classroom_id)

            enrollments = list(qs.order_by("-school_year__start_date", "student__last_name"))
            school_years = list(SchoolYear.objects.order_by("-start_date"))
            classrooms = list(Classroom.objects.filter(is_archived=False).order_by(
                "option__level__order", "option__name", "name"
            ))

        return render(request, self.template_name, {
            "enrollments": enrollments,
            "school_years": school_years,
            "classrooms": classrooms,
            "q": query,
            "year_id": year_id,
            "status_filter": status_filter,
            "classroom_id": classroom_id,
            "EnrollmentStatus": EnrollmentStatus,
            "school": school,
        })


@method_decorator(login_required, name="dispatch")
class EnrollmentCreateView(SchoolAdminMixin, View):
    """Création d'une nouvelle inscription élève."""
    template_name = "students/enrollments/form.html"

    def _build_form_context(self, school, form, selected_year_pk=None):
        from apps.school_years.models import SchoolYear
        from apps.academics.models import Classroom

        with schema_context(school.schema_name):
            school_years = list(SchoolYear.objects.filter(is_archived=False).order_by("-start_date"))
            students = list(Student.objects.filter(status="active").order_by("last_name", "first_name"))

            classrooms = []
            if selected_year_pk:
                classrooms = _get_classrooms_for_year(school, selected_year_pk)

        # Peupler les querysets du formulaire
        from apps.school_years.models import SchoolYear as SY
        from apps.academics.models import Classroom as CL
        form.fields["student"].queryset = Student.objects.filter(pk__in=[s.pk for s in students])
        form.fields["school_year"].queryset = SY.objects.filter(pk__in=[y.pk for y in school_years])
        form.fields["classroom"].queryset = CL.objects.filter(pk__in=[c.pk for c in classrooms])

        return {
            "form": form,
            "school_years": school_years,
            "classrooms": classrooms,
            "students": students,
            "title": "Nouvelle inscription",
            "school": school,
        }

    def get(self, request):
        school = request.user.school
        from apps.school_years.models import SchoolYear
        from apps.academics.models import Classroom

        with schema_context(school.schema_name):
            school_years = list(SchoolYear.objects.filter(is_archived=False).order_by("-start_date"))
            students = list(Student.objects.filter(status="active").order_by("last_name", "first_name"))
            # Année par défaut : l'année active
            active_year = next((y for y in school_years if y.is_active), None)
            selected_year_pk = request.GET.get("year") or (active_year.pk if active_year else None)
            classrooms = _get_classrooms_for_year(school, selected_year_pk) if selected_year_pk else []
            # Élève pré-sélectionné ?
            student_pk = request.GET.get("student")

        form = EnrollmentForm(
            student_queryset=Student.objects.filter(pk__in=[s.pk for s in students]),
            school_year_queryset=SchoolYear.objects.filter(pk__in=[y.pk for y in school_years]),
            classroom_queryset=Classroom.objects.filter(pk__in=[c.pk for c in classrooms]),
            initial={
                "school_year": active_year,
                "student": student_pk,
                "status": EnrollmentStatus.ACTIVE,
            },
        )

        return render(request, self.template_name, {
            "form": form,
            "school_years": school_years,
            "classrooms": classrooms,
            "students": students,
            "title": "Nouvelle inscription",
            "school": school,
            "selected_year_pk": int(selected_year_pk) if selected_year_pk else None,
        })

    def post(self, request):
        school = request.user.school
        from apps.school_years.models import SchoolYear
        from apps.academics.models import Classroom

        with schema_context(school.schema_name):
            school_years = list(SchoolYear.objects.filter(is_archived=False).order_by("-start_date"))
            students = list(Student.objects.filter(status="active").order_by("last_name", "first_name"))
            selected_year_pk = request.POST.get("school_year")
            classrooms = _get_classrooms_for_year(school, selected_year_pk) if selected_year_pk else []

        form = EnrollmentForm(
            request.POST,
            student_queryset=Student.objects.filter(pk__in=[s.pk for s in students]),
            school_year_queryset=SchoolYear.objects.filter(pk__in=[y.pk for y in school_years]),
            classroom_queryset=Classroom.objects.filter(pk__in=[c.pk for c in classrooms]),
        )

        if form.is_valid():
            data = form.cleaned_data
            with schema_context(school.schema_name), transaction.atomic():
                enrollment = StudentEnrollment.objects.create(
                    student=data["student"],
                    school_year=data["school_year"],
                    classroom=data["classroom"],
                    status=data["status"],
                    notes=data.get("notes", ""),
                    enrolled_by=request.user,
                )
            messages.success(
                request,
                f"Inscription de {enrollment.student.get_full_name()} "
                f"dans {enrollment.classroom} créée avec succès."
            )
            return redirect("students:enrollment_detail", pk=enrollment.pk)

        return render(request, self.template_name, {
            "form": form,
            "school_years": school_years,
            "classrooms": classrooms,
            "students": students,
            "title": "Nouvelle inscription",
            "school": school,
            "selected_year_pk": int(selected_year_pk) if selected_year_pk else None,
        })


@method_decorator(login_required, name="dispatch")
class EnrollmentDetailView(SchoolStaffMixin, View):
    """Détail d'une inscription."""
    template_name = "students/enrollments/detail.html"

    def get(self, request, pk):
        school = request.user.school
        with schema_context(school.schema_name):
            enrollment = get_object_or_404(
                StudentEnrollment.objects.select_related(
                    "student", "student__primary_parent",
                    "school_year", "classroom",
                    "classroom__option", "classroom__option__level",
                    "classroom__main_room", "enrolled_by",
                ),
                pk=pk,
            )
            # Historique complet de l'élève
            history = list(
                StudentEnrollment.objects.filter(student=enrollment.student)
                .select_related("school_year", "classroom", "classroom__option", "classroom__option__level")
                .order_by("-school_year__start_date", "-enrollment_date")
            )
        return render(request, self.template_name, {
            "enrollment": enrollment,
            "history": history,
            "EnrollmentStatus": EnrollmentStatus,
            "school": school,
        })


@method_decorator(login_required, name="dispatch")
class EnrollmentEditView(SchoolAdminMixin, View):
    """Modification d'une inscription (statut + notes)."""
    template_name = "students/enrollments/edit.html"

    def get(self, request, pk):
        school = request.user.school
        with schema_context(school.schema_name):
            enrollment = get_object_or_404(
                StudentEnrollment.objects.select_related(
                    "student", "school_year", "classroom",
                    "classroom__option", "classroom__option__level",
                ),
                pk=pk,
            )
        form = EnrollmentEditForm(initial={"status": enrollment.status, "notes": enrollment.notes})
        return render(request, self.template_name, {
            "form": form, "enrollment": enrollment, "school": school,
        })

    def post(self, request, pk):
        school = request.user.school
        with schema_context(school.schema_name):
            enrollment = get_object_or_404(StudentEnrollment, pk=pk)
            form = EnrollmentEditForm(request.POST)
            if form.is_valid():
                new_status = form.cleaned_data["status"]
                # Vérifier l'unicité si on remet l'inscription en état actif
                if new_status in EnrollmentStatus.ACTIVE_STATUSES:
                    conflict = StudentEnrollment.objects.filter(
                        student=enrollment.student,
                        school_year=enrollment.school_year,
                        status__in=EnrollmentStatus.ACTIVE_STATUSES,
                    ).exclude(pk=pk).first()
                    if conflict:
                        form.add_error(
                            "status",
                            f"Impossible : cet élève a déjà une inscription active pour cette année "
                            f"(classe\u00a0: {conflict.classroom}). "
                            f"Annulez d'abord l'inscription existante."
                        )
                        enrollment = get_object_or_404(
                            StudentEnrollment.objects.select_related(
                                "student", "school_year", "classroom",
                                "classroom__option", "classroom__option__level",
                            ),
                            pk=pk,
                        )
                        return render(request, self.template_name, {
                            "form": form, "enrollment": enrollment, "school": school,
                        })
                enrollment.status = new_status
                enrollment.notes = form.cleaned_data["notes"]
                enrollment.save(update_fields=["status", "notes", "updated_at"])
                messages.success(request, "Inscription mise à jour.")
                return redirect("students:enrollment_detail", pk=enrollment.pk)
            enrollment = get_object_or_404(
                StudentEnrollment.objects.select_related(
                    "student", "school_year", "classroom",
                    "classroom__option", "classroom__option__level",
                ),
                pk=pk,
            )
        return render(request, self.template_name, {
            "form": form, "enrollment": enrollment, "school": school,
        })


@method_decorator(login_required, name="dispatch")
class EnrollmentChangeClassView(SchoolAdminMixin, View):
    """
    Changement de classe d'un élève en cours d'année.
    Annule l'inscription courante et crée une nouvelle inscription.
    """
    template_name = "students/enrollments/change_class.html"

    def _get_available_classrooms(self, school, enrollment):
        """Classes disponibles = même année scolaire, actives, pas archivées."""
        from apps.academics.models import Classroom
        with schema_context(school.schema_name):
            return list(
                Classroom.objects.filter(
                    school_year=enrollment.school_year,
                    is_active=True,
                    is_archived=False,
                ).exclude(pk=enrollment.classroom_id)
                .select_related("option", "option__level")
                .order_by("option__level__order", "option__name", "name")
            )

    def get(self, request, pk):
        school = request.user.school
        with schema_context(school.schema_name):
            enrollment = get_object_or_404(
                StudentEnrollment.objects.select_related(
                    "student", "school_year", "classroom",
                    "classroom__option", "classroom__option__level",
                ),
                pk=pk,
            )
            if not enrollment.is_active_enrollment:
                messages.error(request, "Seule une inscription active peut faire l'objet d'un changement de classe.")
                return redirect("students:enrollment_detail", pk=pk)

            classrooms = self._get_available_classrooms(school, enrollment)

        from apps.academics.models import Classroom
        form = ChangeClassForm(
            classroom_queryset=Classroom.objects.filter(pk__in=[c.pk for c in classrooms]),
            current_classroom=enrollment.classroom,
        )
        return render(request, self.template_name, {
            "form": form, "enrollment": enrollment, "classrooms": classrooms, "school": school,
        })

    def post(self, request, pk):
        school = request.user.school
        with schema_context(school.schema_name):
            enrollment = get_object_or_404(StudentEnrollment, pk=pk)
            if not enrollment.is_active_enrollment:
                messages.error(request, "Seule une inscription active peut faire l'objet d'un changement de classe.")
                return redirect("students:enrollment_detail", pk=pk)

            classrooms = self._get_available_classrooms(school, enrollment)

        from apps.academics.models import Classroom
        form = ChangeClassForm(
            request.POST,
            classroom_queryset=Classroom.objects.filter(pk__in=[c.pk for c in classrooms]),
            current_classroom=enrollment.classroom,
        )

        if form.is_valid():
            new_classroom = form.cleaned_data["new_classroom"]
            reason = form.cleaned_data.get("reason", "")
            with schema_context(school.schema_name), transaction.atomic():
                # Clore l'inscription actuelle
                old_notes = enrollment.notes
                enrollment.status = EnrollmentStatus.COMPLETED
                enrollment.notes = (
                    f"{old_notes}\n[Changement de classe vers {new_classroom}]"
                    if old_notes
                    else f"[Changement de classe vers {new_classroom}]"
                )
                enrollment.save(update_fields=["status", "notes", "updated_at"])
                # Créer la nouvelle inscription
                new_enrollment = StudentEnrollment.objects.create(
                    student=enrollment.student,
                    school_year=enrollment.school_year,
                    classroom=new_classroom,
                    status=EnrollmentStatus.ACTIVE,
                    notes=f"Changement de classe depuis {enrollment.classroom}. {reason}".strip(". "),
                    enrolled_by=request.user,
                )
            messages.success(
                request,
                f"{enrollment.student.get_full_name()} a été transféré(e) dans {new_classroom}."
            )
            return redirect("students:enrollment_detail", pk=new_enrollment.pk)

        with schema_context(school.schema_name):
            enrollment = get_object_or_404(
                StudentEnrollment.objects.select_related(
                    "student", "school_year", "classroom",
                    "classroom__option", "classroom__option__level",
                ),
                pk=pk,
            )
        return render(request, self.template_name, {
            "form": form, "enrollment": enrollment, "classrooms": classrooms, "school": school,
        })


@method_decorator(login_required, name="dispatch")
class EnrollmentStatusChangeView(SchoolAdminMixin, View):
    """Changement rapide du statut d'une inscription (via POST)."""

    def post(self, request, pk):
        school = request.user.school
        with schema_context(school.schema_name):
            enrollment = get_object_or_404(StudentEnrollment, pk=pk)
            new_status = request.POST.get("status", "").strip()

            if new_status not in dict(EnrollmentStatus.CHOICES):
                messages.error(request, "Statut invalide.")
                return redirect("students:enrollment_detail", pk=pk)

            # Empêcher deux inscriptions actives sur la même année
            if new_status in EnrollmentStatus.ACTIVE_STATUSES:
                conflict = StudentEnrollment.objects.filter(
                    student=enrollment.student,
                    school_year=enrollment.school_year,
                    status__in=EnrollmentStatus.ACTIVE_STATUSES,
                ).exclude(pk=pk).first()
                if conflict:
                    messages.error(
                        request,
                        f"Impossible : cet élève a déjà une inscription active pour cette année scolaire "
                        f"(classe : {conflict.classroom})."
                    )
                    return redirect("students:enrollment_detail", pk=pk)

            enrollment.status = new_status
            enrollment.save(update_fields=["status", "updated_at"])
            messages.success(request, f"Statut mis à jour : {enrollment.get_status_display()}.")

        return redirect("students:enrollment_detail", pk=pk)


@method_decorator(login_required, name="dispatch")
class ClassroomEnrollmentsView(SchoolStaffMixin, View):
    """Liste des élèves inscrits dans une classe donnée."""
    template_name = "students/enrollments/classroom_list.html"

    def get(self, request, classroom_pk):
        school = request.user.school
        from apps.academics.models import Classroom

        with schema_context(school.schema_name):
            classroom = get_object_or_404(
                Classroom.objects.select_related("option", "option__level", "school_year"),
                pk=classroom_pk,
            )
            enrollments = list(
                StudentEnrollment.objects.filter(classroom=classroom)
                .select_related("student", "student__primary_parent", "school_year")
                .order_by("student__last_name", "student__first_name")
            )
            active_count = sum(1 for e in enrollments if e.status in EnrollmentStatus.ACTIVE_STATUSES)

        return render(request, self.template_name, {
            "classroom": classroom,
            "enrollments": enrollments,
            "active_count": active_count,
            "EnrollmentStatus": EnrollmentStatus,
            "school": school,
        })


# ---------------------------------------------------------------------------
# Phase 3.1 — API HTMX : classes dynamiques selon l'année scolaire
# ---------------------------------------------------------------------------

@method_decorator(login_required, name="dispatch")
class ClassroomsForYearView(SchoolStaffMixin, View):
    """
    Retourne les classes d'une année scolaire (JSON) pour chargement dynamique HTMX.
    """

    def get(self, request):
        school = request.user.school
        year_id = request.GET.get("year_id", "").strip()
        if not year_id:
            return JsonResponse({"classrooms": []})

        classrooms = _get_classrooms_for_year(school, year_id)
        return JsonResponse({
            "classrooms": [
                {
                    "pk": c.pk,
                    "label": str(c),
                    "full_name": c.full_name,
                    "capacity": c.capacity,
                }
                for c in classrooms
            ]
        })


# ---------------------------------------------------------------------------
# Phase 3.1 — Recherche HTMX d'élèves
# ---------------------------------------------------------------------------

@method_decorator(login_required, name="dispatch")
class StudentSearchView(SchoolStaffMixin, View):
    """Recherche dynamique d'élèves (JSON) pour le formulaire d'inscription."""

    def get(self, request):
        school = request.user.school
        query = request.GET.get("q", "").strip()
        if len(query) < 2:
            return JsonResponse({"students": []})

        with schema_context(school.schema_name):
            qs = Student.objects.filter(
                Q(matricule__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query),
                status="active",
            ).select_related("primary_parent")[:20]
            students = list(qs)

        return JsonResponse({
            "students": [
                {
                    "pk": s.pk,
                    "label": f"{s.last_name} {s.first_name} ({s.matricule})",
                    "matricule": s.matricule,
                    "full_name": s.get_full_name(),
                }
                for s in students
            ]
        })
