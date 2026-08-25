from rest_framework.routers import (
    DefaultRouter,
)

from invoices.api_v1_views import (
    InvoiceV1ViewSet,
)

router = DefaultRouter()

router.register(
    'invoices',
    InvoiceV1ViewSet,
    basename='v1-invoice',
)


urlpatterns = router.urls
