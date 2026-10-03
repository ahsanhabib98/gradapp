from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class AuthenticationTests(APITestCase):
    def test_registration_creates_user_and_profile(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "student1",
                "email": "student1@example.com",
                "first_name": "Test",
                "last_name": "Student",
                "password": "StrongPass!2026",
                "password_confirm": "StrongPass!2026",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="student1")
        self.assertTrue(hasattr(user, "student_profile"))

    def test_login_returns_tokens(self):
        User.objects.create_user(username="student1", password="StrongPass!2026")
        response = self.client.post(
            reverse("login"),
            {"username": "student1", "password": "StrongPass!2026"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_profile_requires_authentication(self):
        response = self.client.get(reverse("student_profile"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_update_profile(self):
        user = User.objects.create_user(username="student1", password="StrongPass!2026")
        self.client.force_authenticate(user=user)
        response = self.client.patch(
            reverse("student_profile"),
            {
                "intended_degree_level": "masters",
                "previous_field_of_study": "Computer Science",
                "gpa": "3.75",
                "research_interests": "Artificial intelligence",
                "funding_requirement": "required",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["intended_degree_level"], "masters")
