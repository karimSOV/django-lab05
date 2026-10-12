from django.contrib import admin

from .models import Genre, Movie, Person, Rating


class RatingInline(admin.TabularInline):
    model = Rating
    extra = 1
    readonly_fields = ["created_at"]


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ["title", "year", "director", "display_genres"]
    list_filter = ["genres", "year"]
    search_fields = ["title", "director__name"]
    filter_horizontal = ["genres"]
    list_select_related = ["director"]
    inlines = [RatingInline]
    readonly_fields = ["created_at", "updated_at"]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("genres")

    @admin.display(description="Genres")
    def display_genres(self, movie):
        return ", ".join(genre.name for genre in movie.genres.all())


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ["movie", "score", "created_at"]
    list_filter = ["score"]
    list_select_related = ["movie"]
    readonly_fields = ["created_at"]


admin.site.site_header = "Movie Administration"
admin.site.site_title = "Movie Administrator"
