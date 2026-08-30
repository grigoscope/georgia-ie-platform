from django.conf import settings
from rest_framework.throttling import (
    AnonRateThrottle,
    ScopedRateThrottle,
    UserRateThrottle,
)


class APIAnonRateThrottle(
    AnonRateThrottle
):
    scope = 'api_anon'

    def get_rate(self):
        return (
            settings.API_THROTTLE_RATES
            .get(self.scope)
        )

    def get_cache_key(
        self,
        request,
        view,
    ):
        if (
            request.user
            and request.user.is_authenticated
        ):
            return None

        ident = self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': (
                f'{ident}:{request.path}'
            ),
        }


class APIUserRateThrottle(
    UserRateThrottle
):
    scope = 'api_user'

    def get_rate(self):
        return (
            settings.API_THROTTLE_RATES
            .get(self.scope)
        )

    def get_cache_key(
        self,
        request,
        view,
    ):
        if (
            not request.user
            or not request.user.is_authenticated
        ):
            return None

        return self.cache_format % {
            'scope': self.scope,
            'ident': (
                f'{request.user.pk}:'
                f'{request.path}'
            ),
        }


class APIScopedRateThrottle(
    ScopedRateThrottle
):
    def get_rate(self):
        if not self.scope:
            return None

        return (
            settings.API_THROTTLE_RATES
            .get(self.scope)
        )