from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="StudentProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("intended_degree_level", models.CharField(blank=True, choices=[("masters", "Master's"), ("doctoral", "Doctoral"), ("other", "Other graduate degree")], max_length=20)),
                ("previous_degree", models.CharField(blank=True, max_length=150)),
                ("previous_field_of_study", models.CharField(blank=True, max_length=150)),
                ("gpa", models.DecimalField(blank=True, decimal_places=2, max_digits=3, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(4)])),
                ("academic_interests", models.TextField(blank=True)),
                ("research_interests", models.TextField(blank=True)),
                ("career_goals", models.TextField(blank=True)),
                ("preferred_programs", models.TextField(blank=True)),
                ("preferred_locations", models.TextField(blank=True)),
                ("tuition_budget", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ("funding_requirement", models.CharField(choices=[("required", "Funding required"), ("preferred", "Funding preferred"), ("not_required", "Funding not required")], default="preferred", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="student_profile", to=settings.AUTH_USER_MODEL)),
            ],
        )
    ]
