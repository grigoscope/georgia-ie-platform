from rest_framework.routers import (
    DefaultRouter,
)

from finances.views import (
    CounterpartyViewSet,
    FinancialAccountViewSet,
)

router = DefaultRouter()

router.register(
    'accounts',
    FinancialAccountViewSet,
    basename='account',
)

router.register(
    'counterparties',
    CounterpartyViewSet,
    basename='counterparty',
)


urlpatterns = router.urls
