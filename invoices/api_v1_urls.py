from django.urls import path
from rest_framework.routers import (
    DefaultRouter,
)

from invoices.api_v1_views import (
    InvoiceV1ViewSet,
)
from invoices.delivery_mixin import (
    InvoiceSharePublicAPIView,
)

router = DefaultRouter()

router.register(
    'invoices',
    InvoiceV1ViewSet,
    basename='v1-invoice',
)


urlpatterns = [
    path(
        'invoice-share/<uuid:token>/',
        InvoiceSharePublicAPIView.as_view(),
        name='invoice-share-public',
    ),
]

urlpatterns += router.urls
