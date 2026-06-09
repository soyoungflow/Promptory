from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prompts', '0005_recipe_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='prompt',
            name='is_blueprint_draft',
            field=models.BooleanField(db_index=True, default=False, verbose_name='설계 초안'),
        ),
    ]
