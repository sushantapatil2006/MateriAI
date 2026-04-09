"""
Root URL configuration for MateriAI backend.
"""
from django.urls import path, include

urlpatterns = [
    path("api/", include("api.urls")),
]
