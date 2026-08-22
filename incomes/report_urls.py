from django.urls import path

from incomes.report_views import (
    AccountsReportAPIView,
    CategoriesReportAPIView,
    CounterpartiesReportAPIView,
    CurrenciesReportAPIView,
    DashboardReportAPIView,
    MonthlyReportAPIView,
    YearlyReportAPIView,
)

urlpatterns = [
    path(
        'dashboard/',
        DashboardReportAPIView.as_view(),
        name='report-dashboard',
    ),
    path(
        'monthly/',
        MonthlyReportAPIView.as_view(),
        name='report-monthly',
    ),
    path(
        'yearly/',
        YearlyReportAPIView.as_view(),
        name='report-yearly',
    ),
    path(
        'accounts/',
        AccountsReportAPIView.as_view(),
        name='report-accounts',
    ),
    path(
        'currencies/',
        CurrenciesReportAPIView.as_view(),
        name='report-currencies',
    ),
    path(
        'counterparties/',
        CounterpartiesReportAPIView.as_view(),
        name='report-counterparties',
    ),
    path(
        'categories/',
        CategoriesReportAPIView.as_view(),
        name='report-categories',
    ),
]
