from functools import cached_property
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib import admin

from backend_django.storage_backends import PublicMediaStorage
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
    socials = models.JSONField("Social media handles", blank=True, default=dict)
    logo = models.ImageField("League logo", upload_to='league_logos/', storage=PublicMediaStorage, blank=True, null=True)
    background = models.ImageField("League page background", upload_to='league_backgrounds/', storage=PublicMediaStorage, blank=True, null=True)

    def __str__(self):
        return f"LocalLeague <{self.slug}>: {self.name}"
    
class Team(models.Model):
    slug = models.SlugField(
        "Unique slug",
        max_length=40, 
        unique=True,
        null=False,
    )
    name = models.CharField("Full name", max_length=40)
    short_name = models.CharField("Short name", max_length=10)
    coach = models.CharField("Coach name", max_length=50, blank=True)
    logo = models.ImageField("Team logo", upload_to='team_logos/', storage=PublicMediaStorage, blank=True, null=True)
    local_league = models.ForeignKey(
        LocalLeague, 
        on_delete=models.PROTECT, 
        related_name='teams',
        verbose_name="Local league to which the team belongs"
    )

    @property
    def pts(self):
        """Calculates total points from all finished matches."""
        return sum(p.points for p in self.match_participations.all() if p.match.finished)

    @property
    def record(self):
        """Calculates the win-draw-loss record."""
        r_wins = p_wins = p_losses = r_losses = 0
        for p in self.match_participations.all():
            if not p.match.finished:
                continue
            res = p.result_type
            if res == 'REGULAR_WIN':
                r_wins += 1
            elif res == 'PENALTY_WIN':
                p_wins += 1
            elif res == 'PENALTY_LOSS':
                p_losses += 1
            elif res == 'REGULAR_LOSS':
                r_losses += 1
        return f"{r_wins}V - {p_wins}VR - {p_losses}SR - {r_losses}S"

    def __str__(self):
        return f"Team <{self.slug}>: {self.name} in local league <{self.local_league.slug}>"
    
class Staff(models.Model):
    role = models.CharField("Role in the league", max_length=50, default="Coordinatore staff")
    instagram = models.CharField("Instagram handle", max_length=50, blank=True)
    isLeader = models.BooleanField("Is this staff member a league leader?", default=False)
    local_league = models.ForeignKey(
        LocalLeague,
        on_delete=models.CASCADE,
        related_name='staff',
        verbose_name="Local league to which the staff member belongs"
    )

class Partner(models.Model):
    name = models.CharField("Partner name", max_length=100)
    logo = models.ImageField("Partner logo", upload_to='partner_logos/', storage=PublicMediaStorage)
    url = models.URLField("Partner website", max_length=200, blank=True)
    local_league = models.ForeignKey(
        LocalLeague,
        on_delete=models.CASCADE,
        related_name='partners',
        verbose_name="Local league to which the partner belongs"
    )

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

class TeamParticipationMatch(models.Model):
    team = models.ForeignKey(
        Team,
        on_delete=models.PROTECT,
        verbose_name="Team participating in the match",
        related_name='match_participations'
    )
    match = models.ForeignKey(
        'Match',
        on_delete=models.CASCADE,
        verbose_name="Match in which the team is participating",
        related_name='participations'
    )
    is_home = models.BooleanField("Is this the home team?", default=False)
    score_offset = models.SmallIntegerField(
        "Score offset for this team",
        default=0,
        help_text="Adjust the displayed score for this team by this offset (can be negative)"
    )
    penalties = models.PositiveSmallIntegerField(
        "Penalties scored by this team",
        default=0,
    )

    @cached_property
    @admin.display(
        description="Computed Score",
        boolean=False,
    )
    def score(self):
        match = self.match
        if match.score_computation_mode == 'OFFSET':
            return self.score_offset
        event_goals = self.events.filter(event_type='GOAL').count()
        if match.score_computation_mode == 'EVENTS':
            return event_goals
        if match.score_computation_mode == 'SUM':
            return event_goals + self.score_offset
        return 0
    
    @property
    def opponent_participation(self):
        """Helper to get the other team's participation in the same match."""
        return self.match.participations.exclude(id=self.id).first()
    
    @property
    def is_winner(self):
        """Returns True if this team won the match (regular time or penalties)."""
        opponent = self.opponent_participation
        if not opponent:
            return False # Should not happen in valid match
        
        my_score = self.score
        op_score = opponent.score

        if my_score > op_score:
            return True
        elif my_score == op_score:
            return self.penalties > opponent.penalties
        return False

    @property
    def result_type(self):
        """
        Returns the type of result:
        'REGULAR_WIN' (3 pts), 'PENALTY_WIN' (2 pts), 
        'PENALTY_LOSS' (1 pt), 'REGULAR_LOSS' (0 pts)
        """
        opponent = self.opponent_participation
        if not opponent:
            return None

        my_score = self.score
        op_score = opponent.score

        if my_score > op_score:
            return 'REGULAR_WIN'
        elif my_score < op_score:
            return 'REGULAR_LOSS'
        else:
            # Scores are tied, check penalties
            if self.penalties > opponent.penalties:
                return 'PENALTY_WIN'
            elif self.penalties < opponent.penalties:
                return 'PENALTY_LOSS'
            else:
                return 'DRAW' # rare case if penalties are equal or not used

    @property
    def points(self):
        """
        Assigns points based on result:
        3 for regular win
        2 for win at penalties
        1 for loss at penalties
        0 for loss at regular time
        """
        res = self.result_type
        if res == 'REGULAR_WIN':
            return 3
        elif res == 'PENALTY_WIN':
            return 2
        elif res == 'PENALTY_LOSS':
            return 1
        return 0

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['team', 'match'], name='unique_team_match_participation'),
            models.UniqueConstraint(fields=['match', 'is_home'], name='unique_home_team_per_match'),
        ]
        ordering = ['-is_home']

    def __str__(self):
        home_away = "Home" if self.is_home else "Away"
        return f"TeamParticipationMatch <{self.id}>: {home_away} team <{self.team.slug}> in match <{self.match.name}>"

class Match(models.Model):
    class Meta:
        verbose_name_plural = "Matches"
        ordering = ['-datetime']

    datetime = models.DateTimeField("Match date and time")
    teams = models.ManyToManyField(
        Team,
        related_name='matches',
        verbose_name="Teams participating in the match",
        through=TeamParticipationMatch,
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

    finished = models.BooleanField("Is the match finished?", default=False)

    @property
    def score_text(self):
        participations = self.participations.all()
        if participations.count() != 2:
            return "N/A"
        home_team = participations.get(is_home=True)
        away_team = participations.get(is_home=False)
        return f"{home_team.score} - {away_team.score}"
    
    @property
    def name(self):
        participations = self.participations.all()
        if participations.count() != 2:
            return "N/A"
        home_team = participations.get(is_home=True)
        away_team = participations.get(is_home=False)
        return f"{home_team.team.name} vs {away_team.team.name}"


    def __str__(self):
        return f"Match <{self.id}>: {self.name} on {self.datetime.strftime('%Y-%m-%d %H:%M')}"
    
class MatchEvent(models.Model):
    team_match = models.ForeignKey(
        TeamParticipationMatch,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name="Match and Team to which the event belongs"
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

    def __str__(self):
        return f"MatchEvent <{self.id}>: {self.event_type} at minute {self.minute} in match {self.team_match.match.id} for team {self.team_match.team.slug}"