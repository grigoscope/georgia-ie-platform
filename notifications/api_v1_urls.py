from django.urls import path
from rest_framework.routers import (
    DefaultRouter,
)

from notifications.api_v1_views import (
    NotificationSettingsAPIView,
    NotificationViewSet,
)

router = DefaultRouter()

router.register(
    'notifications',
    NotificationViewSet,
    basename='v1-notification',
)


urlpatterns = [
    path(
        'notification-settings/',
        (NotificationSettingsAPIView.as_view()),
        name='v1-notification-settings',
    ),
]

urlpatterns += router.urls
