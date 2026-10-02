from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import identify_hasher
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings


class SetupEditorsTests(TestCase):
    username = "test_editor"
    password = "Test-Only!Orbit-7392"

    def run_command(self):
        output = StringIO()
        call_command(
            "setup_editors",
            username=self.username,
            password=self.password,
            stdout=output,
        )
        return output.getvalue()

    def test_editor_has_exact_movie_and_rating_permissions(self):
        self.run_command()
        user = get_user_model().objects.get(username=self.username)
        group = Group.objects.get(name="editores")
        expected = {
            "movies.add_movie",
            "movies.change_movie",
            "movies.view_movie",
            "movies.add_rating",
            "movies.change_rating",
            "movies.view_rating",
        }
        permissions = {
            f"{app_label}.{codename}"
            for app_label, codename in group.permissions.values_list(
                "content_type__app_label", "codename"
            )
        }
        self.assertEqual(permissions, expected)
        self.assertEqual(user.get_all_permissions(), expected)
        self.assertEqual(list(user.groups.all()), [group])
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.has_perm("movies.delete_movie"))
        self.assertFalse(user.has_perm("movies.delete_rating"))

    def test_password_is_hashed_and_not_printed(self):
        output = self.run_command()
        user = get_user_model().objects.get(username=self.username)
        self.assertNotEqual(user.password, self.password)
        self.assertTrue(user.check_password(self.password))
        self.assertIsNotNone(identify_hasher(user.password))
        self.assertNotIn(self.password, output)
        self.assertNotIn(user.password, output)

    def test_repeated_command_is_idempotent_and_removes_extra_permissions(
        self,
    ):
        self.run_command()
        user = get_user_model().objects.get(username=self.username)
        group = Group.objects.get(name="editores")
        original_user_pk = user.pk
        original_group_pk = group.pk
        permissions = set(group.permissions.values_list("pk", flat=True))
        group.permissions.add(
            Permission.objects.get(
                content_type__app_label="movies", codename="delete_movie"
            )
        )
        self.run_command()
        self.assertEqual(
            get_user_model().objects.filter(username=self.username).count(), 1
        )
        self.assertEqual(Group.objects.filter(name="editores").count(), 1)
        user = get_user_model().objects.get(username=self.username)
        self.assertEqual(user.pk, original_user_pk)
        self.assertEqual(
            Group.objects.get(name="editores").pk, original_group_pk
        )
        self.assertEqual(list(user.groups.all()), [group])
        self.assertEqual(
            set(group.permissions.values_list("pk", flat=True)), permissions
        )
        self.assertTrue(user.check_password(self.password))

    def test_existing_editor_password_can_be_updated(self):
        self.run_command()
        replacement = "Test-Only!Comet-8463"
        output = StringIO()
        call_command(
            "setup_editors",
            username=self.username,
            password=replacement,
            stdout=output,
        )
        user = get_user_model().objects.get(username=self.username)
        self.assertTrue(user.check_password(replacement))
        self.assertFalse(user.check_password(self.password))
        self.assertNotIn(replacement, output.getvalue())

    def test_superuser_is_not_demoted_and_group_changes_are_rolled_back(self):
        user = get_user_model().objects.create_superuser(
            username=self.username, password=self.password
        )
        original_password = user.password
        group = Group.objects.create(name="editores")
        permission = Permission.objects.get(
            content_type__app_label="movies", codename="delete_movie"
        )
        group.permissions.add(permission)
        output = StringIO()
        with self.assertRaisesMessage(CommandError, "superuser"):
            call_command(
                "setup_editors",
                username=self.username,
                password="Test-Only!Comet-8463",
                stdout=output,
            )
        user.refresh_from_db()
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertEqual(user.password, original_password)
        self.assertFalse(user.groups.exists())
        self.assertEqual(list(group.permissions.all()), [permission])
        self.assertEqual(output.getvalue(), "")

    def test_superuser_rejection_does_not_leave_a_new_group(self):
        get_user_model().objects.create_superuser(
            username=self.username, password=self.password
        )
        with self.assertRaises(CommandError):
            self.run_command()
        self.assertFalse(Group.objects.filter(name="editores").exists())

    def test_username_and_password_are_required(self):
        options = (
            {},
            {"username": self.username},
            {"password": self.password},
        )
        for arguments in options:
            with self.subTest(arguments=tuple(arguments)):
                with self.assertRaises(CommandError):
                    call_command(
                        "setup_editors", stdout=StringIO(), **arguments
                    )
                self.assertFalse(
                    Group.objects.filter(name="editores").exists()
                )
                self.assertFalse(get_user_model().objects.exists())

    def test_password_validators_reject_without_creating_user_or_group(self):
        cases = (
            ("MinimumLengthValidator", "short"),
            ("CommonPasswordValidator", "password"),
            ("NumericPasswordValidator", "123456789012"),
            ("UserAttributeSimilarityValidator", self.username),
        )
        for validator, password in cases:
            with self.subTest(validator=validator):
                validators = [
                    {
                        "NAME": (
                            "django.contrib.auth.password_validation."
                            f"{validator}"
                        )
                    }
                ]
                output = StringIO()
                with override_settings(AUTH_PASSWORD_VALIDATORS=validators):
                    with self.assertRaises(CommandError):
                        call_command(
                            "setup_editors",
                            username=self.username,
                            password=password,
                            stdout=output,
                        )
                self.assertFalse(
                    Group.objects.filter(name="editores").exists()
                )
                self.assertFalse(get_user_model().objects.exists())
                self.assertEqual(output.getvalue(), "")

    def test_invalid_password_preserves_existing_user_and_permissions(self):
        user = get_user_model().objects.create_user(
            username=self.username, password=self.password, is_staff=False
        )
        original_password = user.password
        group = Group.objects.create(name="editores")
        permission = Permission.objects.get(
            content_type__app_label="movies", codename="delete_rating"
        )
        group.permissions.add(permission)
        with self.assertRaises(CommandError):
            call_command(
                "setup_editors",
                username=self.username,
                password="short",
                stdout=StringIO(),
            )
        user.refresh_from_db()
        self.assertEqual(user.password, original_password)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.groups.exists())
        self.assertEqual(list(group.permissions.all()), [permission])

    def test_invalid_username_leaves_no_user_or_group(self):
        with self.assertRaises(CommandError):
            call_command(
                "setup_editors",
                username="invalid editor!",
                password=self.password,
                stdout=StringIO(),
            )
        self.assertFalse(get_user_model().objects.exists())
        self.assertFalse(Group.objects.filter(name="editores").exists())

    def test_missing_permission_fails_without_creating_user_or_group(self):
        Permission.objects.get(
            content_type__app_label="movies", codename="add_rating"
        ).delete()
        with self.assertRaisesMessage(CommandError, "permissions are missing"):
            self.run_command()
        self.assertFalse(get_user_model().objects.exists())
        self.assertFalse(Group.objects.filter(name="editores").exists())
