import datetime
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
import secrets
from django.contrib.auth.hashers import make_password



# Create your models here.
class Player(models.Model):
    player_list = models.ForeignKey('PlayerList', 
                                    on_delete=models.PROTECT,
                                    related_name='players',
                                    verbose_name="Player list to which the player belongs",
                                    null=True,
                                    blank=True,
                                    default=None)
    user = models.OneToOneField(User, on_delete=models.PROTECT, related_name='player_user')
    first_name = models.CharField("First name", max_length=30, null=True, blank=True)
    last_name = models.CharField("Last name", max_length=30, null=True, blank=True)
    date_of_birth = models.DateField("Date of birth", null=True, blank=True)
    code_fiscal = models.CharField("Fiscal Code", max_length=16, unique=True, null=True, blank=True)
    shirt_number = models.PositiveSmallIntegerField("Shirt number", null=True, blank=True, validators=[
        MaxValueValidator(99, message="Shirt number cannot exceed 99"),
        MinValueValidator(1, message="Shirt number must be at least 1")
    ])
    SHIRT_SIZES = [
        ('XS', 'Extra Small'),
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
        ('XXL', 'Double Extra Large'),
    ]
    POSITIONS = [
        ('POR', 'Portiere'),
        ('DIF', 'Difensore'),
        ('CEN', 'Centrocampista'),
        ('ATT', 'Attaccante'),
    ]
    shirt_size = models.CharField("Shirt size", max_length=5, choices=SHIRT_SIZES, null=True, blank=True)  
    position = models.CharField("Playing position", max_length=5, choices=POSITIONS, null=True, blank=True)  
    privacy_accepted_at = models.DateTimeField("Privacy policy accepted at", null=True, blank=True, default=None)
    REGISTRATION_STATUSES = [
        ('PEND', 'Pending'),
        ('EDIT', 'Editable'),
        ('SUB', 'Submitted'),
    ]
    registration_status = models.CharField("Registration status", max_length=6, choices=REGISTRATION_STATUSES, default='PEND')

    def __str__(self):
        return f"Player {self.first_name} {self.last_name} (Mail: {self.user.email})"
    
class Parent(models.Model):
    first_name = models.CharField("First name", max_length=30)
    last_name = models.CharField("Last name", max_length=30)
    date_of_birth = models.DateField("Date of birth", null=True, blank=True)
    code_fiscal = models.CharField("Fiscal Code", max_length=16)

    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name='parent', verbose_name="Player associated with this parent")

    def __str__(self):
        return f"Parent {self.first_name} {self.last_name}"
    
class PlayerList(models.Model):
    name = models.CharField("Team Name", max_length=50)
    team = models.ForeignKey('matches.Team', 
                             on_delete=models.PROTECT,
                             related_name='registration_player_lists',
                             verbose_name="Team to which the player list belongs",
                             null=True,
                             blank=True,
                             default=None)
    manager = models.OneToOneField(User, on_delete=models.PROTECT, related_name='player_list_manager')
    registration_token = models.CharField("Registration token", max_length=100, unique=True)
    registration_fee = models.DecimalField("Registration fee", max_digits=8, decimal_places=2, default=0.00)
    submitted_at = models.DateTimeField("Submitted at", null=True, blank=True, default=None)

    def save(self, *args, **kwargs):
        if not self.registration_token:
            # generate a URL-safe random token and ensure uniqueness
            token = secrets.token_urlsafe(32)
            while PlayerList.objects.filter(registration_token=token).exists():
                token = secrets.token_urlsafe(32)
            self.registration_token = token
        super().save(*args, **kwargs)

    def __str__(self):
        return f"PlayerList: {self.name}. Managed by {self.manager.email}"
    
class DeletionRequest(models.Model):
    player_to_be_deleted = models.ForeignKey(Player, on_delete=models.SET_NULL, related_name='deletion_requests', null=True, blank=True)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deletion_requests_made')
    requested_at = models.DateTimeField("Requested at", auto_now_add=True)
    deletion_info = models.TextField("Information about deletion request", null=True, blank=True, editable=False)

    status = models.CharField("Status", max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ], default='PENDING')

    def __str__(self):
        return f"Deletion request for {self.player_to_be_deleted.user.email if self.player_to_be_deleted else 'Unknown'} by {self.requested_by.email} at {self.requested_at}"
    
class PasswordResetRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_requests')
    token = models.CharField("Reset token", max_length=64)
    created_at = models.DateTimeField("Created at")
    expires_at = models.DateTimeField("Expires at")
    used_at = models.DateTimeField("Used at", null=True, blank=True)

    #add a computed field to check if the token is used
    @property
    def used(self):
        return self.used_at is not None

    def __str__(self):
        return f"Password reset request for {self.user.email} at {self.created_at} (Used: {self.used})"
    
    @staticmethod
    def create_request(user, duration_days=1):
        token = secrets.token_urlsafe(32)
        hashed_token = make_password(token)
        new_request = PasswordResetRequest.objects.create(
            user=user,
            token=hashed_token,
            created_at=datetime.datetime.now(datetime.timezone.utc),
            expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=duration_days)
        )
        return new_request, token