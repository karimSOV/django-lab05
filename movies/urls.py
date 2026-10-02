from django.urls import path

from . import views


app_name = "movies"

urlpatterns = [
    path(
        "<int:pk>/recommendations/",
        views.recommendations,
        name="recommendations",
    ),
]
