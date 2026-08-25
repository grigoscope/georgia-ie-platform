from django.urls import path

from accounts.profile_views import (
    ProfileAPIView,
    ProfileLogoAPIView,
    ProfileSignatureAPIView,
)

urlpatterns = [
    path(
        'profile/',
        ProfileAPIView.as_view(),
        name='profile',
    ),
    path(
        'profile/signature/',
        ProfileSignatureAPIView.as_view(),
        name='profile-signature',
    ),
    path(
        'profile/logo/',
        ProfileLogoAPIView.as_view(),
        name='profile-logo',
    ),
]
