from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("students", "0002_phase3")]

    operations = [
        migrations.AlterField(
            model_name="student",
            name="matricule",
            field=models.CharField(
                help_text="Généré automatiquement par KLASS.",
                max_length=30,
                unique=True,
                verbose_name="Matricule",
            ),
        ),
    ]