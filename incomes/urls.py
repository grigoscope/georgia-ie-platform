from rest_framework.routers import DefaultRouter

from incomes.views import IncomeEntryViewSet

router = DefaultRouter()

router.register(
    'incomes',
    IncomeEntryViewSet,
    basename='income',
)

urlpatterns = router.urls
