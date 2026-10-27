from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name='WeeklyPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week_start', models.DateField(db_index=True, help_text='Monday of the planned week')),
                ('preferences', models.JSONField(blank=True, default=dict)),
                ('plan_data', models.JSONField(blank=True, default=dict)),
                ('generation_source', models.CharField(choices=[('ai', 'AI generated'), ('template', 'Template fallback')], default='template', max_length=12)),
                ('generation_note', models.CharField(blank=True, default='', max_length=240)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='weekly_plans', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-week_start', '-updated_at']},
        ),
        migrations.AddConstraint(
            model_name='weeklyplan',
            constraint=models.UniqueConstraint(fields=('user', 'week_start'), name='unique_weekly_plan_per_user_week'),
        ),
    ]
