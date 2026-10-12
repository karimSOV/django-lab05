from django.db.models import Avg, Q
from django.shortcuts import get_object_or_404, render

from .models import Movie


def movie_list(request):
    movies = (
        Movie.objects.select_related("director")
        .prefetch_related("genres")
        .annotate(average_score=Avg("ratings__score"))
    )
    query = request.GET.get("q", "").strip()
    if query:
        movies = movies.filter(
            Q(title__icontains=query)
            | Q(director__name__icontains=query)
            | Q(genres__name__icontains=query)
        ).distinct()
    return render(
        request,
        "movies/movie_list.html",
        {"movies": movies, "q": query},
    )


def recommendations(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    recommended_movies = (
        Movie.objects.filter(genres__in=movie.genres.all())
        .exclude(pk=movie.pk)
        .select_related("director")
        .prefetch_related("genres")
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
