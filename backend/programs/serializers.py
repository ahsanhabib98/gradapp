from rest_framework import serializers

from .models import GraduateProgram, University


class UniversitySerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = ("id", "name", "city", "state_or_region", "country", "website_url")


class GraduateProgramSerializer(serializers.ModelSerializer):
    university = UniversitySerializer(read_only=True)
    university_id = serializers.PrimaryKeyRelatedField(
        queryset=University.objects.all(), source="university", write_only=True
    )

    class Meta:
        model = GraduateProgram
        fields = (
            "id",
            "university",
            "university_id",
            "name",
            "degree_level",
            "field_of_study",
            "description",
            "admission_requirements",
            "tuition_per_year",
            "funding_available",
            "funding_details",
            "application_deadline",
            "program_url",
            "source_retrieved_at",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
