"""
Migration Phase 2.1 — Ajout des champs statut sur Classroom et Room.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("academics", "0003_level_is_active_option_is_active"),
    ]

    operations = [
        # Classroom : is_active + is_archived
        migrations.AddField(
            model_name="classroom",
            name="is_active",
            field=models.BooleanField(
                default=True,
                help_text="Une classe inactive n'accepte plus de nouvelles inscriptions.",
                verbose_name="Active",
            ),
        ),
        migrations.AddField(
            model_name="classroom",
            name="is_archived",
            field=models.BooleanField(
                default=False,
                help_text="Une classe archivée est en lecture seule et ne peut plus être modifiée.",
                verbose_name="Archivée",
            ),
        ),
        # Room : code + is_archived + polyvalent type
        migrations.AddField(
            model_name="room",
            name="code",
            field=models.CharField(blank=True, max_length=20, verbose_name="Code"),
        ),
        migrations.AddField(
            model_name="room",
            name="is_archived",
            field=models.BooleanField(
                default=False,
                help_text="Une salle archivée ne peut plus être utilisée.",
                verbose_name="Archivée",
            ),
        ),
        migrations.AlterField(
            model_name="room",
            name="room_type",
            field=models.CharField(
                choices=[
                    ("classroom", "Salle de classe"),
                    ("laboratory", "Laboratoire"),
                    ("computer_lab", "Salle informatique"),
                    ("library", "Bibliothèque"),
                    ("gymnasium", "Gymnase"),
                    ("polyvalent", "Salle polyvalente"),
                    ("other", "Autre"),
                ],
                default="classroom",
                max_length=20,
                verbose_name="Type",
            ),
        ),
    ]
