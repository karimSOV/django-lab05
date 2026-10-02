import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Genre",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
            ],
            options={
                "verbose_name": "genre",
                "verbose_name_plural": "genres",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Person",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200)),
                ("birth_date", models.DateField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "person",
                "verbose_name_plural": "people",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Movie",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                ("year", models.PositiveIntegerField()),
                ("synopsis", models.TextField(blank=True)),
                (
                    "poster",
                    models.ImageField(blank=True, upload_to="posters/"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "genres",
                    models.ManyToManyField(
                        related_name="movies", to="movies.genre"
                    ),
                ),
                (
                    "director",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="directed_movies",
                        to="movies.person",
                    ),
                ),
            ],
            options={
                "verbose_name": "movie",
                "verbose_name_plural": "movies",
                "ordering": ["title", "pk"],
            },
        ),
        migrations.CreateModel(
            name="Rating",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "score",
                    models.IntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(10),
                        ]
                    ),
                ),
                ("comment", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "movie",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ratings",
                        to="movies.movie",
                    ),
                ),
            ],
            options={
                "verbose_name": "rating",
                "verbose_name_plural": "ratings",
                "ordering": ["-created_at", "-pk"],
            },
        ),
    ]
