"""
URL configuration for the API app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path("upload/", views.UploadView.as_view(), name="upload"),
    path("paste/", views.PasteView.as_view(), name="paste"),
    path("grade/<int:material_id>/", views.GradeQuizView.as_view(), name="grade"),
]
