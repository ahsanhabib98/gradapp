from django.contrib import admin

from .models import StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "intended_degree_level",
        "previous_field_of_study",
        "funding_requirement",
        "updated_at",
    )
    list_filter = ("intended_degree_level", "funding_requirement")
    search_fields = ("user__username", "user__email", "research_interests")
