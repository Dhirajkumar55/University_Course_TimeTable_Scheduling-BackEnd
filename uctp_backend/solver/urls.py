from django.urls import path
from . import views

urlpatterns = [
    path('solution/', views.solution),
    path('sol1/', views.csvInputSolution)
]