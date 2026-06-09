from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='task_type',
            field=models.CharField(
                choices=[
                    ('transform', '에이전트 변환'),
                    ('blueprint_design', '설계서 만들기'),
                    ('embed', '임베딩'),
                ],
                max_length=20,
            ),
        ),
    ]
