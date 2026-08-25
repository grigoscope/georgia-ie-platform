from django.urls import path

from incomes.report_views import (
    AccountsReportAPIView,
    CategoriesReportAPIView,
    CurrenciesReportAPIView,
    DashboardReportAPIView,
    MonthlyReportAPIView,
    YearlyReportAPIView,
)

urlpatterns = [
    path(
        'dashboard/',
        DashboardReportAPIView.as_view(),
        name='v1-report-dashboard',
    ),
    path(
        'monthly/',
        MonthlyReportAPIView.as_view(),
        name='v1-report-monthly',
    ),
    path(
        'yearly/',
        YearlyReportAPIView.as_view(),
        name='v1-report-yearly',
    ),
    path(
        'accounts/',
        AccountsReportAPIView.as_view(),
        name='v1-report-accounts',
    ),
    path(
        'currencies/',
        CurrenciesReportAPIView.as_view(),
        name='v1-report-currencies',
    ),
    path(
        'declaration-categories/',
        CategoriesReportAPIView.as_view(),
        name='v1-report-declaration-categories',
    ),
]
