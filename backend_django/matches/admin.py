from django.contrib import admin
from .models import LocalLeague, Stadium, Team, Player

# Register your models here.
@admin.register(LocalLeague)
class LocalLeagueAdmin(admin.ModelAdmin):
    list_display = ('slug', 'name', 'title', 'subtitle')
    search_fields = ('slug', 'name', 'title')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ("name", "title", "subtitle")
    fieldsets = (
        (None, {
            'fields': ('slug', 'name')
        }),
        ('Page Info', {
            'fields': ('title', 'subtitle')
        }),
        # ('Related Info', {
        #     'fields': ('teams', 'stadiums'),
        #     'classes': ('collapse',),
        # }),
    )

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('slug', 'name', 'short_name', 'local_league__name')
    search_fields = ('slug', 'name', 'short_name', 'local_league__name')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ("name", "short_name")
    list_filter = ('local_league__name',)

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('id', 'last_name', 'first_name', 'shirt_number', 'position', 'team__name')
    search_fields = ('first_name', 'last_name', 'shirt_number')
    list_filter = ('position', 'team__local_league__name')
    list_editable = ('first_name', 'last_name', 'shirt_number', 'position')

    search_help_text = "Search by first name, last name, or shirt number."

@admin.register(Stadium)
class StadiumAdmin(admin.ModelAdmin):
    fields = ('name', 'address', ('latitude', 'longitude'), 'local_leagues')
    list_display = ('id', 'name', 'address', 'latitude', 'longitude')
    search_fields = ('name', 'address')
    list_filter = ('local_leagues__name',)
    list_editable = ('name', 'address')
