from django.contrib import admin

from .models import GraduateProgram, University


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "state_or_region", "country")
    search_fields = ("name", "city", "state_or_region", "country")


@admin.register(GraduateProgram)
class GraduateProgramAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "university",
        "degree_level",
        "field_of_study",
        "funding_available",
        "is_active",
    )
    list_filter = ("degree_level", "funding_available", "is_active")
    search_fields = ("name", "university__name", "field_of_study")
