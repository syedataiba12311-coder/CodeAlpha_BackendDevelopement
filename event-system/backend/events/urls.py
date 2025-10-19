from rest_framework import routers
from .views import EventViewSet, RegistrationViewSet

router = routers.DefaultRouter()
router.register(r'events', EventViewSet, basename='events')
router.register(r'registrations', RegistrationViewSet, basename='registrations')

urlpatterns = router.urls
