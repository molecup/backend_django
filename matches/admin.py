from django.contrib import admin
from .models import LocalLeague, Match, MatchEvent, Partner, Stadium, Staff, Team, Player, TeamParticipationMatch
from nested_admin import NestedStackedInline, NestedModelAdmin, NestedTabularInline
from django import forms


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

class MatchEventInline(NestedTabularInline):
    model = MatchEvent
    fk_name = 'team_match'
    extra = 0
    verbose_name = "Event for this Team"
    verbose_name_plural = "Events for this Team"
    show_change_link = False
    fields = ('event_type', 'minute', 'player')


class TeamParticipationMatchInline(NestedTabularInline):
    model = TeamParticipationMatch
    fk_name = 'match'
    verbose_name = "Teams in this Match"
    verbose_name_plural = "Team in this Match"
    can_delete = False
    extra = 2
    max_num = 2
    min_num = 2
    fields = ('team', 'is_home', 'score', 'score_offset', 'penalties')
    readonly_fields = ('score',)
    show_change_link = False

    inlines = (MatchEventInline,)

# Register your models here.

# @admin.register(TeamParticipationMatch)
# class TeamParticipationMatchAdmin(admin.ModelAdmin):
#     list_display = ('id', 'match', 'team', 'is_home', 'score_offset', 'penalties', 'score')
#     list_editable = ('is_home', 'score_offset', 'penalties')
#     search_fields = ('match__id', 'team__name')
#     list_filter = ('team__local_league__name',)
#     readonly_fields = ('score',)
#     inlines = (MatchEventInline,)

class StaffLocalLeagueInline(admin.TabularInline):
    model = Staff
    extra = 1
    verbose_name = "Staff in this Local League"
    verbose_name_plural = verbose_name
    classes = ['collapse']

class PartnerLocalLeagueInline(admin.TabularInline):
    model = Partner
    extra = 1
    verbose_name = "Partners in this Local League"
    verbose_name_plural = verbose_name
    classes = ['collapse']

class LocalLeagueForm(forms.ModelForm):
    instagram = forms.CharField(required=False, label="Instagram Handle")
    tiktok = forms.CharField(required=False, label="TikTok Handle")

    class Meta:
        model = LocalLeague
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate the form fields from the JSON field if instance exists
        if self.instance and self.instance.pk and self.instance.socials:
            self.fields['instagram'].initial = self.instance.socials.get('instagram', '')
            self.fields['tiktok'].initial = self.instance.socials.get('tiktok', '')

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Pack fields back into the JSON field
        instance.socials = {
            'instagram': self.cleaned_data.get('instagram', ''),
            'tiktok': self.cleaned_data.get('tiktok', '')
        }
        if commit:
            instance.save()
        return instance

@admin.register(LocalLeague)
class LocalLeagueAdmin(admin.ModelAdmin):
    list_display = ('slug', 'name', 'title', 'subtitle', 'logo')
    search_fields = ('slug', 'name', 'title')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ("name", "title", "subtitle")
    fieldsets = (
        (None, {
            'fields': ('slug', 'name')
        }),
        ('Page Info', {
            'fields': ('title', 'subtitle', 'instagram', 'tiktok', 'logo', 'background'),
        }),
    )
    inlines = (StaffLocalLeagueInline, PartnerLocalLeagueInline, StadiumLocalLeagueInline, TeamLocalLeagueInline,)
    form = LocalLeagueForm

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('slug', 'name', 'short_name', 'coach', 'local_league__name', 'logo')
    search_fields = ('slug', 'name', 'short_name', 'local_league__name')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ("name", "short_name", 'coach')
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
class MatchAdmin(NestedModelAdmin):
    list_display = ('name', 'score_text', 'datetime', 'stadium', 'finished')
    list_editable = ('datetime', 'stadium', 'finished')
    search_fields = ('teams__name', 'stadium__name')
    list_filter = ('teams__local_league__name',)
    fieldsets = (
        ('General Info', {
            'fields': ('datetime', 'stadium', ('score_computation_mode', 'finished')),
        }),
        ('Registration', {
            'fields': ('registration_required', 'registration_link'),
            'classes': ['collapse'],
        })
    )
    inlines = (TeamParticipationMatchInline,)
