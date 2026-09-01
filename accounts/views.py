from django.conf import settings
from django.contrib.auth import (
    get_user_model,
)
from django.contrib.auth.tokens import (
    default_token_generator,
)
from django.core.mail import send_mail
from django.db import transaction
from django.utils.encoding import (
    force_bytes,
)
from django.utils.http import (
    urlsafe_base64_encode,
)
from rest_framework import (
    generics,
    status,
)
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from rest_framework.response import (
    Response,
)
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import (
    TokenError,
)
from rest_framework_simplejwt.settings import (
    api_settings,
)
from rest_framework_simplejwt.tokens import (
    RefreshToken,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from accounts.serializers import (
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetSerializer,
    RegisterSerializer,
    UserSerializer,
    VersionedTokenObtainPairSerializer,
    VersionedTokenRefreshSerializer,
)

User = get_user_model()


class RegisterAPIView(generics.CreateAPIView):
    """Регистрация."""

    serializer_class = RegisterSerializer

    permission_classes = [
        AllowAny,
    ]

    def create(
        self,
        request,
        *args,
        **kwargs,
    ):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response(
            UserSerializer(user).data,
            status=(status.HTTP_201_CREATED),
        )


class LoginAPIView(TokenObtainPairView):
    """Получить access и refresh."""

    permission_classes = [
        AllowAny,
    ]

    serializer_class = VersionedTokenObtainPairSerializer


class RefreshAPIView(TokenRefreshView):
    """Обновить JWT."""

    permission_classes = [
        AllowAny,
    ]

    serializer_class = VersionedTokenRefreshSerializer


class MeAPIView(generics.RetrieveAPIView):
    """Текущий пользователь."""

    permission_classes = [
        IsAuthenticated,
    ]

    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class LogoutAPIView(APIView):
    """Отозвать текущую JWT-сессию."""

    serializer_class = LogoutSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    @transaction.atomic
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        try:
            refresh = RefreshToken(serializer.validated_data['refresh'])

        except TokenError:
            return Response(
                {'detail': ('Refresh token недействителен.')},
                status=(status.HTTP_400_BAD_REQUEST),
            )

        token_user_id = refresh.get(api_settings.USER_ID_CLAIM)

        if str(token_user_id) != str(request.user.pk):
            return Response(
                {'detail': ('Refresh token принадлежит другому пользователю.')},
                status=(status.HTTP_400_BAD_REQUEST),
            )

        try:
            refresh.blacklist()

        except TokenError:
            return Response(
                {'detail': ('Refresh token уже отозван.')},
                status=(status.HTTP_400_BAD_REQUEST),
            )

        user = User.objects.select_for_update().get(pk=request.user.pk)

        user.token_version += 1

        user.save(
            update_fields=[
                'token_version',
            ]
        )

        return Response(status=(status.HTTP_204_NO_CONTENT))


class PasswordResetAPIView(APIView):
    """
    Запрос сброса.

    Ответ одинаковый независимо
    от существования email.
    """

    serializer_class = PasswordResetSerializer

    permission_classes = [
        AllowAny,
    ]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email'].strip().lower()

        user = User.objects.filter(
            email__iexact=email,
            is_active=True,
        ).first()

        if user is not None:
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            token = default_token_generator.make_token(user)

            frontend_url = getattr(
                settings,
                'PASSWORD_RESET_FRONTEND_URL',
                ('http://localhost:5173/reset-password'),
            )

            reset_url = f'{frontend_url}?uid={uid}&token={token}'

            send_mail(
                subject=('Сброс пароля Georgia IE Platform'),
                message=(f'Для установки нового пароля перейдите по ссылке:\n{reset_url}'),
                from_email=(settings.DEFAULT_FROM_EMAIL),
                recipient_list=[user.email],
                fail_silently=True,
            )

        return Response(
            {
                'detail': (
                    'Если аккаунт с таким email существует, инструкция по сбросу пароля отправлена.'
                )
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmAPIView(APIView):
    """Установить новый пароль."""

    serializer_class = PasswordResetConfirmSerializer

    permission_classes = [
        AllowAny,
    ]

    @transaction.atomic
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(
            {'detail': ('Пароль успешно изменён.')},
            status=status.HTTP_200_OK,
        )
