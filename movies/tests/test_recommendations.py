from django.test import TestCase
from django.urls import reverse

from movies.models import Genre, Movie, Rating


class RecommendationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.adventure = Genre.objects.create(name="Adventure")
        cls.comedy = Genre.objects.create(name="Comedy")
        cls.drama = Genre.objects.create(name="Drama")
        cls.source = Movie.objects.create(title="Source Movie", year=2024)
        cls.source.genres.add(cls.adventure, cls.comedy)
        Rating.objects.create(movie=cls.source, score=10)

    def create_movie(self, title, genres, scores=()):
        movie = Movie.objects.create(title=title, year=2024)
        movie.genres.add(*genres)
        for score in scores:
            Rating.objects.create(movie=movie, score=score)
        return movie

    def get_recommendations(self, movie=None):
        movie = movie or self.source
        response = self.client.get(
            reverse("movies:recommendations", kwargs={"pk": movie.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "movies/recommendations.html")
        self.assertEqual(response.context["movie"], movie)
        return list(response.context["recommendations"])

    def test_source_movie_is_excluded_even_when_highest_rated(self):
        candidate = self.create_movie("Candidate", [self.adventure], [8])
        recommendations = self.get_recommendations()
        self.assertEqual(recommendations, [candidate])
        self.assertNotIn(self.source, recommendations)

    def test_exact_averages_are_sorted_descending(self):
        low = self.create_movie("A Low", [self.adventure], [2, 5])
        high = self.create_movie("Z High", [self.comedy], [8, 10])
        middle = self.create_movie("M Middle", [self.adventure], [4, 9])
        recommendations = self.get_recommendations()
        self.assertEqual(recommendations, [high, middle, low])
        self.assertEqual(
            [movie.average_score for movie in recommendations],
            [9.0, 6.5, 3.5],
        )
        self.assertTrue(
            all(isinstance(movie, Movie) for movie in recommendations)
        )

    def test_other_genres_and_unrated_movies_are_ignored(self):
        candidate = self.create_movie("Rated Match", [self.comedy], [3])
        self.create_movie("Unrelated High Score", [self.drama], [10])
        self.create_movie("Unrated Match", [self.adventure])
        self.create_movie("No Genres", [], [10])
        self.assertEqual(self.get_recommendations(), [candidate])

    def test_missing_movie_returns_404(self):
        missing_pk = self.source.pk + 1000
        self.assertFalse(Movie.objects.filter(pk=missing_pk).exists())
        response = self.client.get(
            reverse("movies:recommendations", kwargs={"pk": missing_pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_only_five_highest_rated_movies_are_returned(self):
        candidates = [
            self.create_movie(f"Candidate {score}", [self.adventure], [score])
            for score in range(1, 8)
        ]
        recommendations = self.get_recommendations()
        self.assertEqual(len(recommendations), 5)
        self.assertEqual(recommendations, list(reversed(candidates))[:5])
        self.assertEqual(
            [movie.average_score for movie in recommendations],
            [7.0, 6.0, 5.0, 4.0, 3.0],
        )

    def test_multiple_shared_genres_do_not_duplicate_or_distort_averages(self):
        shared = self.create_movie(
            "Both Genres", [self.adventure, self.comedy], [2, 9]
        )
        higher = self.create_movie("One Genre", [self.adventure], [6])
        recommendations = self.get_recommendations()
        self.assertEqual(recommendations, [higher, shared])
        self.assertEqual(len({movie.pk for movie in recommendations}), 2)
        self.assertEqual(recommendations[0].average_score, 6.0)
        self.assertEqual(recommendations[1].average_score, 5.5)

    def test_source_without_genres_has_no_recommendations(self):
        source = self.create_movie("No Genres Source", [], [10])
        self.create_movie("Rated Movie", [self.adventure], [8])
        self.assertEqual(self.get_recommendations(source), [])

    def test_source_can_be_unrated(self):
        self.source.ratings.all().delete()
        candidate = self.create_movie("Rated Candidate", [self.adventure], [7])
        self.assertEqual(self.get_recommendations(), [candidate])
