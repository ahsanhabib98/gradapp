from rest_framework.routers import DefaultRouter

from .views import GraduateProgramViewSet, UniversityViewSet


router = DefaultRouter()
router.register("universities", UniversityViewSet, basename="university")
router.register("programs", GraduateProgramViewSet, basename="program")

urlpatterns = router.urls
