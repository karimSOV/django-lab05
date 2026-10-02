from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "genre"
        verbose_name_plural = "genres"

    def __str__(self):
        return self.name


class Person(models.Model):
    name = models.CharField(max_length=200)
    birth_date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "person"
        verbose_name_plural = "people"

    def __str__(self):
        return self.name


class Movie(models.Model):
    title = models.CharField(max_length=200)
    year = models.PositiveIntegerField()
    synopsis = models.TextField(blank=True)
    poster = models.ImageField(upload_to="posters/", blank=True)
    director = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="directed_movies",
    )
    genres = models.ManyToManyField(Genre, related_name="movies")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title", "pk"]
        verbose_name = "movie"
        verbose_name_plural = "movies"

    def __str__(self):
        return self.title


class Rating(models.Model):
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="ratings",
    )
    score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        verbose_name = "rating"
        verbose_name_plural = "ratings"

    def __str__(self):
        return f"{self.movie}: {self.score}/10"
