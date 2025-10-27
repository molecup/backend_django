from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

# Create your models here.
class LocalLeague(models.Model):
    slug = models.SlugField(
        "Unique slug", 
        max_length=20, 
        unique=True,
        null=False, 
    )
    name = models.CharField("Name to be displayed", max_length=50)
    title = models.CharField("Full league page title", max_length=100)
    subtitle = models.CharField("League page subtitle", max_length=200, blank=True)
    

    def __str__(self):
        return f"LocalLeague <{self.slug}>: {self.name}"
    
class Team(models.Model):
    slug = models.SlugField(
        max_length=20, 
        unique=True,
        null=False,
    )
    name = models.CharField("Full name", max_length=50)
    short_name = models.CharField("Short name", max_length=20)
    league = models.ForeignKey(
        LocalLeague, 
        on_delete=models.PROTECT, 
        related_name='teams',
        verbose_name="Local league to which the team belongs"
    )

    def __str__(self):
        return f"Team <{self.slug}>: {self.name} in local league <{self.league.slug}>"
    
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