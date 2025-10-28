from django.contrib import admin
from .models import LocalLeague, Match, MatchEvent, Stadium, Team, Player

# inlines for many-to-many relationships
class StadiumLocalLeagueInline(admin.TabularInline):
    model = Stadium.local_leagues.through
    extra = 1
    verbose_name = "Stadiums in this Local League"
    verbose_name_plural = verbose_name
    classes = ['collapse']

class LocalLeagueStadiumInline(admin.TabularInline):
    model = LocalLeague.stadiums.through
    extra = 1
    verbose_name = "Local Leagues that use this Stadium"
    verbose_name_plural = verbose_name

class TeamLocalLeagueInline(admin.TabularInline):
    model = Team
    fk_name = 'local_league'
    extra = 1
    verbose_name = "Teams in this Local League"
    verbose_name_plural = verbose_name
    show_change_link = True
    classes = ['collapse']

class PlayerTeamInline(admin.TabularInline):
    model = Player
    fk_name = 'team'
    extra = 1
    verbose_name = "Players in this Team"
    verbose_name_plural = verbose_name
    show_change_link = True
    classes = ['collapse']

class MatchEventInline(admin.TabularInline):
    model = MatchEvent
    fk_name = 'match'
    extra = 1
    verbose_name = "Events for this Match"
    verbose_name_plural = verbose_name

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
    )
    inlines = (StadiumLocalLeagueInline, TeamLocalLeagueInline,)

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('slug', 'name', 'short_name', 'local_league__name')
    search_fields = ('slug', 'name', 'short_name', 'local_league__name')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ("name", "short_name")
    list_filter = ('local_league__name',)
    inlines = (PlayerTeamInline,)

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('id', 'last_name', 'first_name', 'shirt_number', 'position', 'team__name')
    search_fields = ('first_name', 'last_name', 'shirt_number')
    list_filter = ('position', 'team__local_league__name')
    list_editable = ('first_name', 'last_name', 'shirt_number', 'position')

    search_help_text = "Search by first name, last name, or shirt number."

@admin.register(Stadium)
class StadiumAdmin(admin.ModelAdmin):
    fields = ('name', 'address', ('latitude', 'longitude'))
    inlines = (LocalLeagueStadiumInline,)
    list_display = ('id', 'name', 'address', 'latitude', 'longitude')
    search_fields = ('name', 'address')
    list_filter = ('local_leagues__name',)
    list_editable = ('name', 'address')

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'home_team', 'home_score', 'away_team', 'away_score', 'date', 'finished')
    list_filter = ('stadium__name', 'home_team__local_league__name', 'away_team__local_league__name')
    search_fields = ('home_team__name', 'away_team__name', 'stadium__name', 'date')
    list_editable = ('date', 'finished')
    fieldsets = (
        ('Match Info', {
            'fields': ('date', 'finished', 'stadium')
        }),
        ('Results', {
            'fields': (('home_team', 'home_team_score_offset', 'home_penalties'), ('away_team', 'away_team_score_offset', 'away_penalties')),
        }),
        ('Registration', {
            'fields': ('registration_required', 'registration_link'),
            'classes': ('collapse',),
        }),
    )
    inlines = (MatchEventInline,)

