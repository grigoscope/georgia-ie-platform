from rest_framework.routers import (
    DefaultRouter,
)

from taxes.api_v1_views import (
    TaxPeriodViewSet,
)

router = DefaultRouter()

router.register(
    'tax-periods',
    TaxPeriodViewSet,
    basename='v1-tax-period',
)


urlpatterns = router.urls
