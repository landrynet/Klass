from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [("students", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="student",
            name="status",
            field=models.CharField(
                choices=[("active", "Actif"), ("inactive", "Inactif"), ("archived", "Archivé")],
                default="active",
                max_length=20,
                verbose_name="Statut",
            ),
        ),
        migrations.AddField(
            model_name="student",
            name="primary_parent",
            field=models.ForeignKey(
                blank=True,
                help_text="Obligatoire lors de la création d'un élève.",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="primary_students",
                to="students.parent",
                verbose_name="Parent / tuteur principal",
            ),
        ),
        migrations.CreateModel(
            name="MatriculeConfiguration",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("prefix", models.CharField(default="KLS", max_length=10, verbose_name="Préfixe")),
                ("include_year", models.BooleanField(default=True, verbose_name="Inclure l'année")),
                ("separator", models.CharField(default="-", max_length=1, verbose_name="Séparateur")),
                ("number_digits", models.PositiveSmallIntegerField(default=4, verbose_name="Nombre de chiffres")),
                ("next_number", models.PositiveIntegerField(default=1, verbose_name="Prochain numéro")),
            ],
            options={"verbose_name": "Configuration des matricules", "verbose_name_plural": "Configuration des matricules"},
        ),
    ]