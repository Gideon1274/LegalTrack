from django.urls import path
from . import views


urlpatterns = [
    path('', views.CaseListCreate.as_view(), name='case-list-create'),
    path('<str:case_id>/', views.CaseRetrieve.as_view(), name='case-retrieve'),
]