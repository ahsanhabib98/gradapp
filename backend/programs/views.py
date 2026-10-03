from django.db.models import Q
from rest_framework import viewsets

from .models import GraduateProgram, University
from .permissions import IsAdminOrReadOnly
from .serializers import GraduateProgramSerializer, UniversitySerializer


class UniversityViewSet(viewsets.ModelViewSet):
    serializer_class = UniversitySerializer
    permission_classes = [IsAdminOrReadOnly]
    queryset = University.objects.all()


class GraduateProgramViewSet(viewsets.ModelViewSet):
    serializer_class = GraduateProgramSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = GraduateProgram.objects.select_related("university").filter(is_active=True)
        params = self.request.query_params

        search = params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(field_of_study__icontains=search)
                | Q(description__icontains=search)
                | Q(university__name__icontains=search)
            )

        if params.get("degree_level"):
            queryset = queryset.filter(degree_level=params["degree_level"])
        if params.get("field"):
            queryset = queryset.filter(field_of_study__icontains=params["field"])
        if params.get("country"):
            queryset = queryset.filter(university__country__iexact=params["country"])
        if params.get("state_or_region"):
            queryset = queryset.filter(
                university__state_or_region__iexact=params["state_or_region"]
            )
        if params.get("funding_available") in {"true", "false"}:
            queryset = queryset.filter(
                funding_available=params["funding_available"] == "true"
            )
        if params.get("max_tuition"):
            try:
                queryset = queryset.filter(tuition_per_year__lte=params["max_tuition"])
            except (TypeError, ValueError):
                pass

        ordering = params.get("ordering")
        allowed_ordering = {
            "name": "name",
            "-name": "-name",
            "tuition": "tuition_per_year",
            "-tuition": "-tuition_per_year",
            "university": "university__name",
        }
        return queryset.order_by(allowed_ordering.get(ordering, "university__name"), "name")
