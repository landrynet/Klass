"""
Migration : ajout du champ school (FK) au modèle User.
Lie les utilisateurs école (school_admin, teacher, etc.) à leur établissement.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
        ("tenants", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="school",
            field=models.ForeignKey(
                blank=True,
                help_text="L'école à laquelle appartient cet utilisateur (null pour le Super Admin).",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="staff",
                to="tenants.school",
                verbose_name="École",
            ),
        ),
    ]
