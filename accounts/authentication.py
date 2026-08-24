from rest_framework_simplejwt.authentication import (
    JWTAuthentication,
)
from rest_framework_simplejwt.exceptions import (
    AuthenticationFailed,
)


class VersionedJWTAuthentication(
    JWTAuthentication
):
    """
    JWT-auth с возможностью инвалидировать
    все ранее выданные токены пользователя.
    """

    def get_user(
        self,
        validated_token,
    ):
        user = super().get_user(
            validated_token
        )

        token_version = (
            validated_token.get(
                'token_version'
            )
        )

        try:
            token_version = int(
                token_version
            )
        except (
            TypeError,
            ValueError,
        ) as error:
            raise AuthenticationFailed(
                'Токен больше не действителен.',
                code='token_revoked',
            ) from error

        if (
            token_version
            != user.token_version
        ):
            raise AuthenticationFailed(
                'Токен больше не действителен.',
                code='token_revoked',
            )

        return user