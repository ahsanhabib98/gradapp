from django.urls import path

from .views import CurrentUserView, RegisterView, StudentProfileView


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("me/", CurrentUserView.as_view(), name="current_user"),
    path("profile/", StudentProfileView.as_view(), name="student_profile"),
]
