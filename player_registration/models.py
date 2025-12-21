import datetime
import io
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator, FileExtensionValidator
import secrets
from django.contrib.auth.hashers import make_password
import csv

from backend_django.storage_backends import PrivateMediaStorage
from matches.models import Team
from django.utils.text import slugify

import logging
logger = logging.getLogger(__name__)



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
    place_of_birth = models.CharField("Place of birth", max_length=64, null=True, blank=True)
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
    email_verified = models.BooleanField("Email verified", default=False)

    def __str__(self):
        return f"Player {self.first_name} {self.last_name} (Mail: {self.user.email})"
    
class Parent(models.Model):
    first_name = models.CharField("First name", max_length=30)
    last_name = models.CharField("Last name", max_length=30)
    date_of_birth = models.DateField("Date of birth", null=True, blank=True)
    place_of_birth = models.CharField("Place of birth", max_length=64, null=True, blank=True)
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
            token = secrets.token_urlsafe(8)
            while PlayerList.objects.filter(registration_token=token).exists():
                token = secrets.token_urlsafe(8)
            self.registration_token = token
        super().save(*args, **kwargs)

    @property
    def  num_submitted_players(self):
        return self.players.filter(registration_status='SUB').count()
    
    @property
    def total_players(self):
        return self.players.count()

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
    token = models.CharField("Reset token", max_length=128)
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
    
class UserMailVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verifications')
    verified_at = models.DateTimeField("Verified at", auto_now_add=True)
    created_at = models.DateTimeField("Created at", auto_now_add=True)
    token = models.CharField("Verification token", max_length=128)

    def __str__(self):
        return f"Verification for {self.user.email} at {self.verified_at}"
    
    @staticmethod
    def create_verification(user):
        token = secrets.token_urlsafe(32)
        hashed_token = make_password(token)
        new_verification = UserMailVerification.objects.create(
            user=user,
            token=hashed_token,
        )
        return new_verification, token
    
class BulkUploads(models.Model):
    uploaded_at = models.DateTimeField("Uploaded at", auto_now_add=True)
    processed_at = models.DateTimeField("Processed at", null=True, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bulk_uploads')
    local_league = models.ForeignKey('matches.LocalLeague', on_delete=models.CASCADE, related_name='bulk_uploads')
    processed = models.BooleanField("Processed", default=False)
    processed_wo_errors = models.BooleanField("Processed without errors", null=True)
    processing_errors = models.TextField("Processing errors", blank=True, default='')
    file = models.FileField("Upload file", upload_to='bulk_upload_player_lists/', storage=PrivateMediaStorage())
    team_name_column = models.CharField("Team name column", max_length=50, default='Squadra (nome completo)')
    team_name_short_column = models.CharField("Team short name column", max_length=50, default='Squadra (abbreviazione 3 lettere)')
    manager_email_column = models.CharField("Manager email column", max_length=50, default='Mail referente squadra')
    separator = models.CharField("CSV Separator", max_length=5, default=';')

    def __str__(self):
        return f"Bulk upload of {self.local_league.name} at {self.uploaded_at} (Processed: {self.processed})"

    def process_bulk_upload(self):
        def process_file(file):
            csv_file = csv.reader(file, delimiter=self.separator)
            header = [x.strip() for x in next(csv_file)]
            team_name_idx = header.index(self.team_name_column.strip())
            team_name_short_idx = header.index(self.team_name_short_column.strip())
            manager_email_idx = header.index(self.manager_email_column.strip())
            for row_id, row in enumerate(csv_file):
                team_name = row[team_name_idx].strip()
                team_name_short = row[team_name_short_idx].strip()
                manager_email = row[manager_email_idx].strip()
                try:
                    if manager_email == '':
                        raise Exception(f"Row {row_id + 2}: Manager email is empty.")
                    if team_name == '':
                        raise Exception(f"Row {row_id + 2}: Team name is empty.")
                    if team_name_short == '':
                        raise Exception(f"Row {row_id + 2}: Team short name is empty.")
                    # check if the user exists, if not create it
                    user, user_created = User.objects.get_or_create(username=manager_email, email=manager_email)

                    if not user_created and hasattr(user, 'player_list_manager'):
                        raise Exception(f"User {manager_email} already has a player list assigned.")
                    
                    # check if a team with that name exists, if not create it
                    team, team_created = Team.objects.get_or_create(slug=slugify(team_name), name=team_name, short_name=team_name_short, local_league=self.local_league)

                    # check if the player list exists, if it does fail
                    player_list, pl_created = PlayerList.objects.get_or_create(manager=user)
                    if not pl_created:
                        raise Exception(f"User {manager_email} already has a player list assigned.")

                    player_list.name = team_name
                    player_list.team = team
                    player_list.save()
                except Exception as e:
                    self.processing_errors += f"Row {row_id + 2}: Error processing row: {str(e)}\n"
                    self.processed_wo_errors = False
                    continue
        self.processing_errors = ''
        self.processed_wo_errors = True
        with self.file.open('rb') as raw_file:
            with io.TextIOWrapper(raw_file, encoding='utf-8-sig') as f:
                try:
                    process_file(f)
                except ValueError as e:
                    self.processing_errors += f"Error: {str(e)}\n"
                    self.processed_wo_errors = False
        self.processed = True
        self.processed_at = datetime.datetime.now(datetime.timezone.utc)
        self.save()

class MedicalCertificate(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name='medical_certificate', primary_key=True)
    uploaded_at = models.DateTimeField("Uploaded at", auto_now_add=True)
    expires_at = models.DateField("Expires at", null=True)
    submitted_at = models.DateTimeField("Submitted at", null=True, blank=True)
    file = models.FileField("Medical certificate file", upload_to='medical_certificates/', storage=PrivateMediaStorage(),
                            validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])])

    def __str__(self):
        return f"Medical Certificate for {self.player.user.email} uploaded at {self.uploaded_at}"
    
    def is_valid(self):
        if self.expires_at < datetime.date.today():
            return False
        return True
    
    def delete(self, *args, **kwargs):
        #delete the file from storage
        self.file.delete(save=False)
        return super().delete(*args, **kwargs)
    
    def mark_as_submitted(self):
        self.submitted_at = datetime.datetime.now(datetime.timezone.utc)
        self.save()