from django.core.validators import MinValueValidator
from django.db import models


class University(models.Model):
    name = models.CharField(max_length=255, unique=True)
    city = models.CharField(max_length=120)
    state_or_region = models.CharField(max_length=120)
    country = models.CharField(max_length=120, default="United States")
    website_url = models.URLField()

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "universities"

    def __str__(self):
        return self.name


class GraduateProgram(models.Model):
    class DegreeLevel(models.TextChoices):
        MASTERS = "masters", "Master's"
        DOCTORAL = "doctoral", "Doctoral"
        OTHER = "other", "Other graduate degree"

    university = models.ForeignKey(
        University, on_delete=models.CASCADE, related_name="programs"
    )
    name = models.CharField(max_length=255)
    degree_level = models.CharField(max_length=20, choices=DegreeLevel.choices)
    field_of_study = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    admission_requirements = models.TextField(blank=True)
    tuition_per_year = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    funding_available = models.BooleanField(default=False)
    funding_details = models.TextField(blank=True)
    application_deadline = models.DateField(null=True, blank=True)
    program_url = models.URLField()
    source_retrieved_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("university__name", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("university", "name", "degree_level"),
                name="unique_program_per_university_and_degree",
            )
        ]

    def __str__(self):
        return f"{self.name} at {self.university.name}"
