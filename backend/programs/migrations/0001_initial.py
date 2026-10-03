from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="University",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
                ("city", models.CharField(max_length=120)),
                ("state_or_region", models.CharField(max_length=120)),
                ("country", models.CharField(default="United States", max_length=120)),
                ("website_url", models.URLField()),
            ],
            options={"verbose_name_plural": "universities", "ordering": ("name",)},
        ),
        migrations.CreateModel(
            name="GraduateProgram",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("degree_level", models.CharField(choices=[("masters", "Master's"), ("doctoral", "Doctoral"), ("other", "Other graduate degree")], max_length=20)),
                ("field_of_study", models.CharField(max_length=180)),
                ("description", models.TextField(blank=True)),
                ("admission_requirements", models.TextField(blank=True)),
                ("tuition_per_year", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ("funding_available", models.BooleanField(default=False)),
                ("funding_details", models.TextField(blank=True)),
                ("application_deadline", models.DateField(blank=True, null=True)),
                ("program_url", models.URLField()),
                ("source_retrieved_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("university", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="programs", to="programs.university")),
            ],
            options={"ordering": ("university__name", "name")},
        ),
        migrations.AddConstraint(
            model_name="graduateprogram",
            constraint=models.UniqueConstraint(fields=("university", "name", "degree_level"), name="unique_program_per_university_and_degree"),
        ),
    ]
