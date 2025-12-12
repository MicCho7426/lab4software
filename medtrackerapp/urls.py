from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MedicationViewSet, DoseLogViewSet, DoctorNoteViewSet

router = DefaultRouter()
router.register("medications", MedicationViewSet, basename="medication")
router.register("logs", DoseLogViewSet, basename="doselog")

router.register("notes", DoctorNoteViewSet, basename="doctornote")

urlpatterns = [
    path("", include(router.urls)),
]