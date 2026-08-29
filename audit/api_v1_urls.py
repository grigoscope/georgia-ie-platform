from django.urls import path

from audit.api_v1_views import (
    AuditLogListAPIView,
)

urlpatterns = [
    path(
        'audit/',
        AuditLogListAPIView.as_view(),
        name='v1-audit-list',
    ),
]
