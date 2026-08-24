from django.urls import path

from accounts.views import (
    LoginAPIView,
    LogoutAPIView,
    MeAPIView,
    PasswordResetAPIView,
    PasswordResetConfirmAPIView,
    RefreshAPIView,
    RegisterAPIView,
)


urlpatterns = [
    path(
        'register/',
        RegisterAPIView.as_view(),
        name='auth-register',
    ),
    path(
        'login/',
        LoginAPIView.as_view(),
        name='auth-login',
    ),
    path(
        'token/refresh/',
        RefreshAPIView.as_view(),
        name='auth-token-refresh',
    ),
    path(
        'logout/',
        LogoutAPIView.as_view(),
        name='auth-logout',
    ),
    path(
        'me/',
        MeAPIView.as_view(),
        name='auth-me',
    ),
    path(
        'password/reset/',
        PasswordResetAPIView.as_view(),
        name='auth-password-reset',
    ),
    path(
        'password/reset/confirm/',
        PasswordResetConfirmAPIView.as_view(),
        name=(
            'auth-password-reset-confirm'
        ),
    ),
]