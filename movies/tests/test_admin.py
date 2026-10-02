from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from movies.models import Genre, Movie, Rating


class EditorAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command(
            "setup_editors",
            username="admin_test_editor",
            password="Test-Only!Orbit-7392",
            stdout=StringIO(),
        )
        cls.editor = get_user_model().objects.get(username="admin_test_editor")
        cls.genre = Genre.objects.create(name="Adventure")
        cls.movie = Movie.objects.create(title="Editor Movie", year=2024)
        cls.movie.genres.add(cls.genre)
        cls.rating = Rating.objects.create(
            movie=cls.movie, score=4, comment="Original rating"
        )

    def setUp(self):
        self.client.force_login(self.editor)

    def test_movie_list_is_accessible_without_delete_action(self):
        response = self.client.get(reverse("admin:movies_movie_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.movie.title)
        action_form = response.context["action_form"]
        if action_form is not None:
            actions = dict(action_form.fields["action"].choices)
            self.assertNotIn("delete_selected", actions)
        self.assertNotContains(response, 'value="delete_selected"')

    def test_movie_change_page_has_no_delete_button(self):
        response = self.client.get(
            reverse("admin:movies_movie_change", args=[self.movie.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["has_delete_permission"])
        self.assertNotContains(response, 'class="deletelink"')
        self.assertNotContains(
            response,
            reverse("admin:movies_movie_delete", args=[self.movie.pk]),
        )
        inline = response.context["inline_admin_formsets"][0]
        self.assertFalse(inline.has_delete_permission)
        self.assertNotIn("DELETE", inline.formset.forms[0].fields)

    def test_direct_movie_and_rating_deletion_is_forbidden(self):
        for model, instance in (
            ("movie", self.movie),
            ("rating", self.rating),
        ):
            url = reverse(f"admin:movies_{model}_delete", args=[instance.pk])
            for method in ("get", "post"):
                with self.subTest(model=model, method=method):
                    response = getattr(self.client, method)(
                        url, {"post": "yes"}
                    )
                    self.assertEqual(response.status_code, 403)
                    self.assertTrue(
                        type(instance).objects.filter(pk=instance.pk).exists()
                    )

    def test_user_and_group_lists_are_forbidden(self):
        for model in ("user", "group"):
            with self.subTest(model=model):
                response = self.client.get(
                    reverse(f"admin:auth_{model}_changelist")
                )
                self.assertEqual(response.status_code, 403)

    def test_editor_can_add_movie_with_rating_inline(self):
        response = self.client.post(
            reverse("admin:movies_movie_add"),
            {
                "title": "New Editor Movie",
                "year": "2025",
                "genres": [str(self.genre.pk)],
                "ratings-TOTAL_FORMS": "1",
                "ratings-INITIAL_FORMS": "0",
                "ratings-MIN_NUM_FORMS": "0",
                "ratings-MAX_NUM_FORMS": "1000",
                "ratings-0-score": "8",
                "ratings-0-comment": "Added inline",
                "_save": "Save",
            },
        )
        self.assertRedirects(
            response, reverse("admin:movies_movie_changelist")
        )
        movie = Movie.objects.get(title="New Editor Movie")
        self.assertEqual(movie.year, 2025)
        self.assertEqual(list(movie.genres.all()), [self.genre])
        rating = movie.ratings.get()
        self.assertEqual(rating.score, 8)
        self.assertEqual(rating.comment, "Added inline")

    def test_editor_can_change_and_add_ratings_inline(self):
        response = self.client.post(
            reverse("admin:movies_movie_change", args=[self.movie.pk]),
            {
                "title": "Updated Editor Movie",
                "year": "2024",
                "genres": [str(self.genre.pk)],
                "ratings-TOTAL_FORMS": "2",
                "ratings-INITIAL_FORMS": "1",
                "ratings-MIN_NUM_FORMS": "0",
                "ratings-MAX_NUM_FORMS": "1000",
                "ratings-0-id": str(self.rating.pk),
                "ratings-0-movie": str(self.movie.pk),
                "ratings-0-score": "9",
                "ratings-0-comment": "Updated inline",
                "ratings-1-score": "7",
                "ratings-1-comment": "Second inline rating",
                "_save": "Save",
            },
        )
        self.assertRedirects(
            response, reverse("admin:movies_movie_changelist")
        )
        self.movie.refresh_from_db()
        self.rating.refresh_from_db()
        self.assertEqual(self.movie.title, "Updated Editor Movie")
        self.assertEqual(self.rating.score, 9)
        self.assertEqual(self.rating.comment, "Updated inline")
        self.assertEqual(self.movie.ratings.count(), 2)
        self.assertTrue(
            self.movie.ratings.filter(
                score=7, comment="Second inline rating"
            ).exists()
        )

    def test_movie_and_rating_timestamps_are_read_only(self):
        response = self.client.get(
            reverse("admin:movies_movie_change", args=[self.movie.pk])
        )
        self.assertEqual(response.status_code, 200)
        admin_form = response.context["adminform"]
        for field in ("created_at", "updated_at"):
            with self.subTest(field=field):
                self.assertIn(field, admin_form.readonly_fields)
                self.assertNotIn(field, admin_form.form.fields)
        inline = response.context["inline_admin_formsets"][0]
        self.assertIn("created_at", inline.readonly_fields)
        for form in inline.formset.forms:
            self.assertNotIn("created_at", form.fields)
        response = self.client.get(
            reverse("admin:movies_rating_change", args=[self.rating.pk])
        )
        self.assertEqual(response.status_code, 200)
        admin_form = response.context["adminform"]
        self.assertIn("created_at", admin_form.readonly_fields)
        self.assertNotIn("created_at", admin_form.form.fields)
