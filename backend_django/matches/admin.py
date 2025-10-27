from django.contrib import admin
from .models import LocalLeague, Team, Player

# Register your models here.
@admin.register(LocalLeague)
class LocalLeagueAdmin(admin.ModelAdmin):
    list_display = ('slug', 'name', 'title')
    search_fields = ('slug', 'name', 'title')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('slug', 'name', 'short_name', 'league')
    search_fields = ('slug', 'name', 'short_name', 'league__name')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ("name", "short_name")

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('id', 'last_name', 'first_name', 'shirt_number', 'position', 'team')
    search_fields = ('first_name', 'last_name', 'shirt_number')
    list_filter = ('position', 'team__league')
    list_editable = ('first_name', 'last_name', 'shirt_number', 'position')

    search_help_text = "Search by first name, last name, or shirt number."
