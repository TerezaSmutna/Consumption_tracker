# meters/urls.py
from django.urls import path, reverse_lazy
from django.views.generic import RedirectView
from .views import MeterListView, ReadingDetailView, ReadingCreateView, ReadingUpdateView, ReportView, OverviewView, MeterTypeOverviewView
from . import views

urlpatterns = [
    path("", RedirectView.as_view(url=reverse_lazy("meter_list"), permanent=False)),  # redirect from /
    path("meters/", MeterListView.as_view(), name="meter_list"),
    path("overview/", OverviewView.as_view(), name="overview"),
    path("overview/<int:pk>/", MeterTypeOverviewView.as_view(), name="meter_type_detail"),
    path("meters/<slug:slug>/", ReadingDetailView.as_view(), name="reading_detail"),
    path("meters/<slug:slug>/add/", ReadingCreateView.as_view(), name="reading_add"),
    path("meters/<slug:slug>/edit/", ReadingUpdateView.as_view(), name="reading_edit"),
    path("report/", ReportView.as_view(), name="report"),
    path('overview/export-pdf/', views.overview_export_pdf, name='overview_export_pdf'),
]
