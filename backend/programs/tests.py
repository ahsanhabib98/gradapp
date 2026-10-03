from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import GraduateProgram, University


User = get_user_model()


class ProgramApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="student", password="StrongPass!2026")
        self.admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="StrongPass!2026"
        )
        self.university = University.objects.create(
            name="Example University",
            city="Corpus Christi",
            state_or_region="Texas",
            country="United States",
            website_url="https://example.edu",
        )
        self.program = GraduateProgram.objects.create(
            university=self.university,
            name="Data Science",
            degree_level="masters",
            field_of_study="Data Science",
            tuition_per_year=20000,
            funding_available=True,
            program_url="https://example.edu/data-science",
        )

    def test_program_list_requires_authentication(self):
        response = self.client.get(reverse("program-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_search_and_filter(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse("program-list"),
            {"search": "Data", "degree_level": "masters", "funding_available": "true"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_regular_user_cannot_create_program(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("program-list"),
            {
                "university_id": self.university.id,
                "name": "Artificial Intelligence",
                "degree_level": "masters",
                "field_of_study": "Artificial Intelligence",
                "program_url": "https://example.edu/ai",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_program(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("program-list"),
            {
                "university_id": self.university.id,
                "name": "Artificial Intelligence",
                "degree_level": "masters",
                "field_of_study": "Artificial Intelligence",
                "program_url": "https://example.edu/ai",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
