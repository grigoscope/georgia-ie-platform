from django.contrib.auth import (
    get_user_model,
)
from django.contrib.auth.password_validation import (
    validate_password,
)
from django.contrib.auth.tokens import (
    default_token_generator,
)
from django.utils.encoding import (
    force_str,
)
from django.utils.http import (
    urlsafe_base64_decode,
)
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import (
    InvalidToken,
    TokenError,
)
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.settings import (
    api_settings,
)
from rest_framework_simplejwt.tokens import (
    RefreshToken,
)


User = get_user_model()


class RegisterSerializer(
    serializers.Serializer
):
    """Регистрация пользователя."""

    email = serializers.EmailField()

    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    password_confirm = (
        serializers.CharField(
            write_only=True,
            trim_whitespace=False,
        )
    )

    def validate_email(
        self,
        value,
    ):
        value = (
            value
            .strip()
            .lower()
        )

        if User.objects.filter(
            email__iexact=value
        ).exists():
            raise serializers.ValidationError(
                'Пользователь с таким '
                'email уже существует.'
            )

        return value

    def validate(self, attrs):
        password = attrs['password']

        if (
            password
            != attrs['password_confirm']
        ):
            raise serializers.ValidationError(
                {
                    'password_confirm': (
                        'Пароли не совпадают.'
                    )
                }
            )

        validate_password(password)

        return attrs

    def create(
        self,
        validated_data,
    ):
        return User.objects.create_user(
            email=validated_data[
                'email'
            ],
            password=validated_data[
                'password'
            ],
        )


class UserSerializer(
    serializers.ModelSerializer
):
    """Текущий пользователь."""

    class Meta:
        model = User

        fields = [
            'id',
            'email',
            'date_joined',
        ]

        read_only_fields = fields


class VersionedTokenObtainPairSerializer(
    TokenObtainPairSerializer
):
    """JWT с версией пользователя."""

    @classmethod
    def get_token(
        cls,
        user,
    ):
        token = super().get_token(user)

        token['token_version'] = (
            user.token_version
        )

        return token

    def validate(self, attrs):
        username_field = (
            self.username_field
        )

        if username_field in attrs:
            attrs[username_field] = (
                attrs[username_field]
                .strip()
                .lower()
            )

        return super().validate(attrs)


class VersionedTokenRefreshSerializer(
    TokenRefreshSerializer
):
    """
    Refresh разрешён только если
    версия токена совпадает с User.
    """

    def validate(self, attrs):
        try:
            refresh = RefreshToken(
                attrs['refresh']
            )

        except TokenError as error:
            raise InvalidToken(
                'Refresh token недействителен.'
            ) from error

        user_id = refresh.get(
            api_settings.USER_ID_CLAIM
        )

        token_version = refresh.get(
            'token_version'
        )

        if (
            user_id is None
            or token_version is None
        ):
            raise InvalidToken(
                'Refresh token недействителен.'
            )

        try:
            user = User.objects.get(
                **{
                    (
                        api_settings
                        .USER_ID_FIELD
                    ): user_id,
                }
            )

        except User.DoesNotExist as error:
            raise InvalidToken(
                'Пользователь не найден.'
            ) from error

        if not user.is_active:
            raise InvalidToken(
                'Пользователь неактивен.'
            )

        try:
            token_version = int(
                token_version
            )
        except (
            TypeError,
            ValueError,
        ) as error:
            raise InvalidToken(
                'Refresh token недействителен.'
            ) from error

        if (
            token_version
            != user.token_version
        ):
            raise InvalidToken(
                'Refresh token был отозван.'
            )

        return super().validate(attrs)


class LogoutSerializer(
    serializers.Serializer
):
    """Выход из аккаунта."""

    refresh = serializers.CharField()


class PasswordResetSerializer(
    serializers.Serializer
):
    """Запрос сброса пароля."""

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(
    serializers.Serializer
):
    """Установка нового пароля."""

    uid = serializers.CharField()

    token = serializers.CharField()

    new_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    new_password_confirm = (
        serializers.CharField(
            write_only=True,
            trim_whitespace=False,
        )
    )

    def validate(self, attrs):
        if (
            attrs['new_password']
            != attrs[
                'new_password_confirm'
            ]
        ):
            raise serializers.ValidationError(
                {
                    'new_password_confirm': (
                        'Пароли не совпадают.'
                    )
                }
            )

        try:
            user_id = force_str(
                urlsafe_base64_decode(
                    attrs['uid']
                )
            )

            user = User.objects.get(
                pk=user_id
            )

        except (
            ValueError,
            TypeError,
            OverflowError,
            User.DoesNotExist,
        ) as error:
            raise serializers.ValidationError(
                {
                    'token': (
                        'Ссылка сброса '
                        'недействительна.'
                    )
                }
            ) from error

        if not (
            default_token_generator
            .check_token(
                user,
                attrs['token'],
            )
        ):
            raise serializers.ValidationError(
                {
                    'token': (
                        'Ссылка сброса '
                        'недействительна '
                        'или устарела.'
                    )
                }
            )

        validate_password(
            attrs['new_password'],
            user=user,
        )

        attrs['user'] = user

        return attrs

    def save(self):
        user = self.validated_data[
            'user'
        ]

        user.set_password(
            self.validated_data[
                'new_password'
            ]
        )

        user.token_version += 1

        user.save(
            update_fields=[
                'password',
                'token_version',
            ]
        )

        return user