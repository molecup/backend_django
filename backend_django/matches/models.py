from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
# from location_field.models.plain import PlainLocationField

# Create your models here.
class LocalLeague(models.Model):
    slug = models.SlugField(
        "Unique slug", 
        max_length=20, 
        unique=True,
        null=False, 
    )
    name = models.CharField("Local League Name", max_length=50)
    title = models.CharField("League page full title", max_length=100)
    subtitle = models.CharField("League page subtitle", max_length=200, blank=True)
    

    def __str__(self):
        return f"LocalLeague <{self.slug}>: {self.name}"
    
class Team(models.Model):
    slug = models.SlugField(
        "Unique slug",
        max_length=20, 
        unique=True,
        null=False,
    )
    name = models.CharField("Full name", max_length=50)
    short_name = models.CharField("Short name", max_length=20)
    local_league = models.ForeignKey(
        LocalLeague, 
        on_delete=models.PROTECT, 
        related_name='teams',
        verbose_name="Local league to which the team belongs"
    )

    def __str__(self):
        return f"Team <{self.slug}>: {self.name} in local league <{self.local_league.slug}>"
    
class Player(models.Model):
    POSITIONS = [
        ('POR', 'Portiere'),
        ('DIF', 'Difensore'),
        ('CEN', 'Centrocampista'),
        ('ATT', 'Attaccante'),
    ]
    first_name = models.CharField("First name", max_length=30)
    last_name = models.CharField("Last name", max_length=30)
    shirt_number = models.PositiveSmallIntegerField(
        "Shirt number", 
        validators=[
            MaxValueValidator(99, message="Shirt number cannot exceed 99"),
            MinValueValidator(1, message="Shirt number must be at least 1") 
            ]
    )
    position = models.CharField("Playing position", max_length=5, choices=POSITIONS, null=True, blank=True)
    team = models.ForeignKey(
        Team, 
        on_delete=models.CASCADE, 
        related_name='players',
        verbose_name="Team to which the player belongs"
    )

    def __str__(self):
        return f"Player <{self.id}>: {self.first_name} {self.last_name} (#{self.shirt_number}) in team <{self.team.slug}>"
    
class Stadium(models.Model):
    name = models.CharField("Stadium name", max_length=100)
    address = models.CharField("Stadium address", max_length=100)
    latitude = models.DecimalField("Stadium latitude", max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField("Stadium longitude", max_digits=9, decimal_places=6, null=True, blank=True)
    local_leagues = models.ManyToManyField(
        LocalLeague,
        related_name='stadiums',
        verbose_name="Local leagues that use this stadium"
    )

    def __str__(self):
        return f"Stadium <{self.id}>: {self.name}"
    
class Match(models.Model):
    class Meta:
        verbose_name_plural = "Matches"
        ordering = ['-date']

    date = models.DateTimeField("Match date and time")
    home_team = models.ForeignKey(
        Team,
        on_delete=models.PROTECT,
        related_name='home_matches',
        verbose_name="Home team"
    )
    away_team = models.ForeignKey(
        Team,
        on_delete=models.PROTECT,
        related_name='away_matches',
        verbose_name="Away team"
    )
    stadium = models.ForeignKey(
        Stadium,
        on_delete=models.SET_NULL,
        related_name='matches',
        verbose_name="Stadium where the match is played",
        null=True,
        blank=True,
    )
    registration_required = models.BooleanField("Is registration available for this match?", default=False)
    registration_link = models.URLField("Registration link", max_length=200, blank=True, null=True)
    home_team_score_offset = models.SmallIntegerField(
        "Home team score offset", 
        default=0,
        help_text="Adjust the displayed score for the home team by this offset (can be negative)"
    )
    away_team_score_offset = models.SmallIntegerField(
        "Away team score offset",
        default=0,
        help_text="Adjust the displayed score for the away team by this offset (can be negative)"
    )
    SCORE_COMPUTATION_MODES = [
        ('EVENTS', 'Automatic from events'),
        ('OFFSET', 'Manual offset only'),
        ('SUM', 'Sum of events and offset'),
    ]
    score_computation_mode = models.CharField(
        "Score computation mode",
        max_length=10,
        choices=SCORE_COMPUTATION_MODES,
        default='EVENTS',
        help_text="Method to compute the displayed score"
    )

    home_penalties = models.PositiveSmallIntegerField(
        "Home team penalties scored",
        default=0,
        help_text="Number of penalties scored by the home team"
    )
    away_penalties = models.PositiveSmallIntegerField(
        "Away team penalties scored",
        default=0,
        help_text="Number of penalties scored by the away team"
    )
    finished = models.BooleanField("Is the match finished?", default=False)

    @property
    def home_score(self):
        if self.score_computation_mode == 'OFFSET':
            return self.home_team_score_offset
        event_goals = self.events.filter(event_type='GOAL', team='HOME').count()
        if self.score_computation_mode == 'EVENTS':
            return event_goals
        if self.score_computation_mode == 'SUM':
            return event_goals + self.home_team_score_offset
        return 0
    
    @property
    def away_score(self):
        if self.score_computation_mode == 'OFFSET':
            return self.away_team_score_offset
        event_goals = self.events.filter(event_type='GOAL', team='AWAY').count()
        if self.score_computation_mode == 'EVENTS':
            return event_goals
        if self.score_computation_mode == 'SUM':
            return event_goals + self.away_team_score_offset
        return 0


    def __str__(self):
        return f"Match <{self.id}>: {self.home_team.name} vs {self.away_team.name} on {self.date.strftime('%Y-%m-%d %H:%M')}"
    
class MatchEvent(models.Model):
    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name="Match to which the event belongs"
    )
    minute = models.PositiveSmallIntegerField(
        "Minute of the event", 
        validators=[
            MaxValueValidator(120, message="Minute cannot exceed 120"),
            MinValueValidator(0, message="Minute must be at least 0")
        ],
        help_text="Enter the minute of the event (0-120)",
        null=True,
        blank=True,
    )
    player = models.ForeignKey(
        Player,
        on_delete=models.SET_NULL,
        related_name='match_events',
        verbose_name="Player involved in the event",
        null=True,
        blank=True,
    )
    EVENT_TYPES = [
        ('GOAL', 'Goal'),
        ('YELLOW_CARD', 'Yellow Card'),
        ('RED_CARD', 'Red Card'),
    ]
    event_type = models.CharField(
        "Type of event",
        max_length=15,
        choices=EVENT_TYPES,
        default='GOAL',
        help_text="Select the type of event"
    )
    TEAM_CHOICES = [
        ('HOME', 'Home Team'),
        ('AWAY', 'Away Team'),
    ]
    team = models.CharField(
        "Team of the player",
        max_length=5,
        choices=TEAM_CHOICES,
        help_text="Select whether the player belongs to the home or away team"
    )

    def __str__(self):
        return f"MatchEvent <{self.id}>: {self.event_type} at minute {self.minute} in match <{self.match.id}>"