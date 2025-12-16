# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('users/', views.user_management, name='user_management'),
    path('users/new/', views.create_staff_account, name='create_staff_account'),
    path('users/<int:user_id>/edit/', views.edit_staff_account, name='edit_staff_account'),
    path('users/<int:user_id>/toggle-active/', views.toggle_staff_active, name='toggle_staff_active'),
    path('users/<int:user_id>/resend-activation/', views.resend_activation, name='resend_activation'),
    path('audit-logs/', views.audit_logs, name='audit_logs'),
    path('audit-logs/export.csv', views.export_audit_logs_csv, name='export_audit_logs_csv'),
    path('accounts/set-password/', views.set_password_view, name='set_password'),
    path('submit/', views.submit_case, name='submit_case'),
    path('case/<str:tracking_id>/step/<int:step>/', views.case_wizard, name='case_wizard'),
    path('case/<str:tracking_id>/edit/', views.edit_case, name='edit_case'),
    path('case/<str:tracking_id>/', views.case_detail, name='case_detail'),
    path('case/<str:tracking_id>/receive/', views.receive_case, name='receive_case'),
    path('case/<str:tracking_id>/return/', views.return_case, name='return_case'),
    path('case/<str:tracking_id>/assign/', views.assign_case, name='assign_case'),
]