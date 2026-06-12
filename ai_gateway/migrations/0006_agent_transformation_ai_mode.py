from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_gateway', '0005_blueprint_design_index_names'),
    ]

    operations = [
        migrations.AddField(
            model_name='agenttransformation',
            name='ai_mode',
            field=models.CharField(
                choices=[('mock', 'mock'), ('real', 'real')],
                default='mock',
                max_length=10,
                verbose_name='AI 실행 모드',
            ),
        ),
    ]
