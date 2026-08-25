from django.urls import path

from telegram_integration.api_v1_views import (
    TelegramLinkAPIView,
    TelegramMiniAppAuthAPIView,
    TelegramWebhookAPIView,
)

urlpatterns = [
    path(
        'telegram/link/',
        TelegramLinkAPIView.as_view(),
        name='telegram-link',
    ),
    path(
        'telegram/mini-app/auth/',
        TelegramMiniAppAuthAPIView.as_view(),
        name='telegram-mini-app-auth',
    ),
    path(
        'telegram/webhook/',
        TelegramWebhookAPIView.as_view(),
        name='telegram-webhook',
    ),
]
