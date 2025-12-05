from rest_framework.routers import DefaultRouter
from .views import MedicationViewSet, DoseLogViewSet, NoteViewSet

router = DefaultRouter()
router.register(r'medications', MedicationViewSet)
router.register(r'logs', DoseLogViewSet)
router.register(r'notes', NoteViewSet)

urlpatterns = router.urls