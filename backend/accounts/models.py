from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class StudentProfile(models.Model):
    class DegreeLevel(models.TextChoices):
        MASTERS = "masters", "Master's"
        DOCTORAL = "doctoral", "Doctoral"
        OTHER = "other", "Other graduate degree"

    class FundingRequirement(models.TextChoices):
        REQUIRED = "required", "Funding required"
        PREFERRED = "preferred", "Funding preferred"
        NOT_REQUIRED = "not_required", "Funding not required"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    intended_degree_level = models.CharField(
        max_length=20, choices=DegreeLevel.choices, blank=True
    )
    previous_degree = models.CharField(max_length=150, blank=True)
    previous_field_of_study = models.CharField(max_length=150, blank=True)
    gpa = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(4)],
    )
    academic_interests = models.TextField(blank=True)
    research_interests = models.TextField(blank=True)
    career_goals = models.TextField(blank=True)
    preferred_programs = models.TextField(blank=True)
    preferred_locations = models.TextField(blank=True)
    tuition_budget = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    funding_requirement = models.CharField(
        max_length=20,
        choices=FundingRequirement.choices,
        default=FundingRequirement.PREFERRED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.username}"
