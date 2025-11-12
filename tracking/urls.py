from django.urls import path
from . import views


urlpatterns = [
    path('transitions/<str:case_id>/', views.CaseTransitionsList.as_view(), name='case-transitions'),
]