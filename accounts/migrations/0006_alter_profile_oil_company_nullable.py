# Generated manually for role/company model update

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_profile_avatar"),
        ("companies", "0002_alter_oilcompany_options_alter_oilcompany_name_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="oil_company",
            field=models.ForeignKey(
                blank=True,
                null=True,
                error_messages={
                    "blank": "Выберите нефтяную компанию.",
                    "invalid": "Выберите корректную нефтяную компанию.",
                },
                on_delete=django.db.models.deletion.CASCADE,
                related_name="employees",
                to="companies.oilcompany",
                verbose_name="Нефтяная компания",
            ),
        ),
    ]