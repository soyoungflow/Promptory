# Generated manually to keep AI model choices aligned with the UI.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prompts', '0002_alter_prompt_is_deleted'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prompt',
            name='ai_model',
            field=models.CharField(
                choices=[
                    ('gpt-5-5', 'GPT-5.5'),
                    ('gpt-5-5-instant', 'GPT-5.5 Instant'),
                    ('claude-opus-4-7', 'Claude Opus 4.7'),
                    ('claude-sonnet-4-6', 'Claude Sonnet 4.6'),
                    ('gemini-3-1-pro', 'Gemini 3.1 Pro'),
                    ('gemini-3-0-flash', 'Gemini 3.0 Flash'),
                    ('other', '기타'),
                ],
                default='other',
                max_length=30,
                verbose_name='AI 모델',
            ),
        ),
    ]
