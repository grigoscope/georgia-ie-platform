from functools import wraps

from idempotency.services import (
    IdempotencyService,
)


def idempotent(view_method):
    @wraps(view_method)
    def wrapper(
        self,
        request,
        *args,
        **kwargs,
    ):
        key = request.headers.get(
            'Idempotency-Key',
            '',
        ).strip()

        if not key:
            return view_method(
                self,
                request,
                *args,
                **kwargs,
            )

        scope = f'{request.method}:{request.path}'

        return IdempotencyService.execute(
            user=request.user,
            key=key,
            scope=scope,
            request_data=request.data,
            callback=lambda: view_method(
                self,
                request,
                *args,
                **kwargs,
            ),
        )

    return wrapper
