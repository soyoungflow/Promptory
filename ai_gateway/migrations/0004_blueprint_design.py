import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prompts', '0006_prompt_is_blueprint_draft'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ai_gateway', '0003_quality_strategy_summary'),
    ]

    operations = [
        migrations.CreateModel(
            name='BlueprintDesign',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, default='', max_length=200, verbose_name='제목')),
                ('brief', models.TextField(verbose_name='자동화 요청')),
                ('extra_context', models.TextField(blank=True, default='', verbose_name='추가 맥락')),
                ('status', models.CharField(
                    choices=[
                        ('pending', '대기'),
                        ('processing', '처리 중'),
                        ('success', '완료'),
                        ('fail', '실패'),
                    ],
                    db_index=True,
                    default='pending',
                    max_length=20,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('recipe', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='from_blueprint_designs',
                    to='prompts.prompt',
                    verbose_name='등록된 레시피',
                )),
                ('source_prompt', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='blueprint_design',
                    to='prompts.prompt',
                    verbose_name='내부 초안 프롬프트',
                )),
                ('transformation', models.OneToOneField(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='blueprint_design',
                    to='ai_gateway.agenttransformation',
                    verbose_name='변환 결과',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='blueprint_designs',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='작성자',
                )),
            ],
            options={
                'verbose_name': '설계서 만들기',
                'verbose_name_plural': '설계서 만들기 목록',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='blueprintdesign',
            index=models.Index(fields=['user', '-created_at'], name='ai_gateway__user_id_6e0f0d_idx'),
        ),
        migrations.AddIndex(
            model_name='blueprintdesign',
            index=models.Index(fields=['status', '-created_at'], name='ai_gateway__status_8a2c1e_idx'),
        ),
    ]
