from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Create or update an editor account and its movie permissions."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--password", required=True)

    def handle(self, *args, **options):
        permission_names = [
            "add_movie",
            "change_movie",
            "view_movie",
            "add_rating",
            "change_rating",
            "view_rating",
        ]
        permissions = Permission.objects.filter(
            content_type__app_label="movies",
            codename__in=permission_names,
        )
        if permissions.count() != len(permission_names):
            raise CommandError("Movie permissions are missing. Run migrate.")

        try:
            with transaction.atomic():
                group, group_created = Group.objects.get_or_create(
                    name="editores",
                )
                group.permissions.set(permissions)
                user, user_created = get_user_model().objects.get_or_create(
                    username=options["username"],
                )
                if user.is_superuser:
                    raise CommandError("A superuser cannot become an editor.")
                user.full_clean(exclude=["password"])
                validate_password(options["password"], user)
                user.set_password(options["password"])
                user.is_staff = True
                user.is_superuser = False
                user.save()
                user.groups.add(group)
        except ValidationError as error:
            raise CommandError("; ".join(error.messages)) from error

        group_status = "Created" if group_created else "Updated"
        user_status = "Created" if user_created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"{group_status} group: {group.name}\n"
                f"{user_status} editor: {user.username}\n"
                f"Permissions: {', '.join(permission_names)}\n"
                "Staff access enabled; superuser access disabled."
            )
        )
