from django.test import TestCase
from django.urls import reverse

from movies.models import Genre, Movie, Person, Rating


class MovieListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.action = Genre.objects.create(name="Action")
        cls.comedy = Genre.objects.create(name="Comedy")
        cls.director = Person.objects.create(name="Jane Director")
        cls.first = Movie.objects.create(
            title="First Movie", year=2020, director=cls.director
        )
        cls.first.genres.add(cls.action, cls.comedy)
        cls.second = Movie.objects.create(title="Second Movie", year=2021)
        cls.second.genres.add(cls.comedy)
        Rating.objects.create(movie=cls.first, score=8)
        Rating.objects.create(movie=cls.first, score=10)

    def search(self, query):
        response = self.client.get(reverse("movies:movie_list"), {"q": query})
        self.assertEqual(response.status_code, 200)
        return list(response.context["movies"])

    def test_root_redirects_to_catalog(self):
        response = self.client.get("/")
        self.assertRedirects(response, reverse("movies:movie_list"))

    def test_catalog_lists_movies_with_average_score(self):
        response = self.client.get(reverse("movies:movie_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "movies/movie_list.html")
        movies = list(response.context["movies"])
        self.assertEqual(movies, [self.first, self.second])
        self.assertEqual(movies[0].average_score, 9.0)
        self.assertIsNone(movies[1].average_score)

    def test_search_by_title(self):
        self.assertEqual(self.search("second"), [self.second])

    def test_search_by_director(self):
        self.assertEqual(self.search("jane"), [self.first])

    def test_search_by_genre_does_not_duplicate_or_distort_average(self):
        movies = self.search("com")
        self.assertEqual(movies, [self.first, self.second])
        self.assertEqual(movies[0].average_score, 9.0)

    def test_search_without_matches_shows_message(self):
        response = self.client.get(
            reverse("movies:movie_list"), {"q": "zzzz"}
        )
        self.assertEqual(list(response.context["movies"]), [])
        self.assertContains(response, "Sin resultados")
