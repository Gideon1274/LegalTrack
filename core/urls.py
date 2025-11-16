# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('submit/', views.submit_case, name='submit_case'),
    path('case/<str:tracking_id>/', views.case_detail, name='case_detail'),
]