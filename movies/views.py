from django.db.models import Avg
from django.shortcuts import get_object_or_404, render

from .models import Movie


def recommendations(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    recommended_movies = (
        Movie.objects.filter(genres__in=movie.genres.all())
        .exclude(pk=movie.pk)
        .annotate(average_score=Avg("ratings__score"))
        .filter(average_score__isnull=False)
        .distinct()
        .order_by("-average_score", "title", "pk")[:5]
    )
    return render(
        request,
        "movies/recommendations.html",
        {"movie": movie, "recommendations": recommended_movies},
    )
