from django.urls import path

from uploads.views import (
    FileDeleteAPIView,
    FileDownloadLinkAPIView,
    FileUploadAPIView,
    PublicFileDownloadAPIView,
)

urlpatterns = [
    path(
        'files/',
        FileUploadAPIView.as_view(),
        name='v1-file-upload',
    ),
    path(
        'files/<int:pk>/download-link/',
        FileDownloadLinkAPIView.as_view(),
        name='v1-file-download-link',
    ),
    path(
        'files/<int:pk>/',
        FileDeleteAPIView.as_view(),
        name='v1-file-delete',
    ),
    path(
        'files/download/<str:token>/',
        PublicFileDownloadAPIView.as_view(),
        name='public-file-download',
    ),
]
