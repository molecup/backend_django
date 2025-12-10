import datetime
import logging
from .mailer import send_deletion_request_notification, send_email_verification_email, send_password_reset_email
from  django.contrib.auth.hashers import check_password

logger = logging.getLogger(__name__)

from rest_framework import serializers
from .models import DeletionRequest, MedicalCertificate, PasswordResetRequest, Player, Parent, PlayerList, UserMailVerification
from django.contrib.auth.models import User

class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = ['first_name', 'last_name', 'date_of_birth', 'place_of_birth', 'code_fiscal']
        
class PlayerListRestrictedSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerList
        fields = ['id', 'name', 'registration_fee', 'submitted_at']

class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email']

class PlayerSerializer(serializers.ModelSerializer):
    parent = ParentSerializer(required=False, allow_null=True)
    player_list = PlayerListRestrictedSerializer(read_only=True)
    user = UserShortSerializer(read_only=True)
    email_verified = serializers.ReadOnlyField()

    class Meta:
        model = Player
        fields = [
            'id', 'user', 'first_name', 'last_name', 'date_of_birth', 'place_of_birth', 'privacy_accepted_at', 'registration_status',
            'code_fiscal', 'shirt_number', 'shirt_size', 'position', 'parent', 'player_list', 'email_verified'
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        player = self.instance
        #prevent submission status change to SUB if email is not verified
        if player and player.registration_status != 'SUB' and attrs.get('registration_status') == 'SUB':
            if not player.email_verified:
                raise serializers.ValidationError("Cannot submit registration: email not verified.")
        return attrs
    

    def create(self, validated_data):
        parent_data = validated_data.pop('parent', None)
        parent_instance = None
        if parent_data:
            parent_instance = Parent.objects.create(**parent_data)
        player_instance = Player.objects.create(parent=parent_instance, **validated_data)
        return player_instance

    def update(self, instance, validated_data):
        parent_data = validated_data.pop('parent', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if parent_data:
            if hasattr(instance, 'parent'):
                for attr, value in parent_data.items():
                    setattr(instance.parent, attr, value)
                instance.parent.save()
            else:
                parent_instance = Parent.objects.create(**parent_data, player=instance)
                instance.parent = parent_instance

        if parent_data is None and hasattr(instance, 'parent'):
            instance.parent.delete()
            instance.parent = None

        instance.save()
        return instance

class PlayerRegistrationSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    mail = serializers.EmailField(write_only=True)
    player_list_token = serializers.CharField(write_only=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        # check if player list with given token exists
        registration_token = attrs.get('player_list_token')
        if not PlayerList.objects.filter(registration_token=registration_token).exists():
            raise serializers.ValidationError("Invalid player list registration token.")
        # check if mail is already used
        mail = attrs.get('mail')
        if User.objects.filter(email=mail).exists():
            raise serializers.ValidationError("Email is already in use.")
        # check if the playerlist is submitted already
        player_list = PlayerList.objects.get(registration_token=registration_token)
        if player_list.submitted_at is not None:
            raise serializers.ValidationError("Cannot register new players to a submitted player list.")
        return attrs

    def create(self, validated_data):

        mail = validated_data.pop('mail')
        password = validated_data.pop('password')
        registration_token = validated_data.pop('player_list_token')

        user = User.objects.create_user(username=mail, email=mail, password=password)
        player_list = PlayerList.objects.get(registration_token=registration_token)

        player = Player.objects.create(user=user, player_list=player_list)

        verification, token = UserMailVerification.create_verification(user)
        send_email_verification_email(verification, token)
        return player
    
class PlayerShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ['id', 'first_name', 'last_name']
    
class PlayerRegistrationForManagerSerializer(serializers.Serializer):
    player = PlayerShortSerializer(read_only=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get('request')
        if not hasattr(request.user, 'player_list_manager'):
            raise serializers.ValidationError("User is not a player list manager.")
        if hasattr(request.user, 'player_user'):
            raise serializers.ValidationError("Player already registered for this user.")
        # check if the player list is submitted already
        player_list = request.user.player_list_manager
        if player_list.submitted_at is not None:
            raise serializers.ValidationError("Cannot register new players to a submitted player list.")

        return attrs
    
    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        player_list = user.player_list_manager
        player = Player.objects.create(user=user, player_list=player_list, email_verified=True)
        return {'player': player}

    


class PlayerListShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerList
        fields = ['id', 'name']

class UserSerializer(serializers.ModelSerializer):
    player_user = PlayerShortSerializer(read_only=True)
    player_list_manager = PlayerListShortSerializer(read_only=True)
    class Meta:
        model = User
        fields = ['id', 'email', 'player_user', 'player_list_manager']

class PlayerForListSerializer(serializers.ModelSerializer):
    first_name = serializers.ReadOnlyField()
    last_name = serializers.ReadOnlyField()
    date_of_birth = serializers.ReadOnlyField()
    email = serializers.ReadOnlyField(source='user.email')
    id = serializers.IntegerField()
    class Meta:
        model = Player
        fields = ['id', 'first_name', 'last_name', 'email', 'date_of_birth', 'shirt_number', 'shirt_size', 'position', 'registration_status']

class PlayerListSerializer(serializers.ModelSerializer):
    registration_token = serializers.ReadOnlyField()
    registration_fee = serializers.ReadOnlyField()
    submitted_at = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()
    players = PlayerForListSerializer(many=True, read_only=False)

    class Meta:
        model = PlayerList
        fields = ['id', 'name', 'registration_token', 'registration_fee', 'submitted_at', 'players']

    def update(self, instance, validated_data):
        # Prevent updates to registration_token, registration_fee, and submitted_at
        players = validated_data.pop('players', [])
        for player_data in players:
            player_id = player_data.get('id')
            try:
                player_instance = instance.players.get(id=player_id)
                logger.debug(f"Updating player {player_id} with data: {player_data}")
                for attr, value in player_data.items():
                    if attr in ["shirt_number", "shirt_size", "position"]:
                        setattr(player_instance, attr, value)
                player_instance.save()
            except Player.DoesNotExist:
                raise serializers.ValidationError(f"Player with id {player_id} does not exist in this player list. With data: {players}")
                continue  # or handle the error as needed
        return super().update(instance, validated_data)
    
    
class DeletionRequestSerializer(serializers.ModelSerializer):
    status = serializers.ReadOnlyField()
    requested_at = serializers.ReadOnlyField()
    requested_by = serializers.PrimaryKeyRelatedField(read_only=True)
    player_info = PlayerForListSerializer(source='player_to_be_deleted', read_only=True)



    class Meta:
        model = DeletionRequest
        fields = ['id', 'player_to_be_deleted', 'requested_at', 'requested_by', 'status', 'player_info']

    def validate(self, attrs):
        # check if a pending deletion request already exists for the user
        player = attrs.get('player_to_be_deleted')
        if DeletionRequest.objects.filter(player_to_be_deleted=player, status='PENDING').exists():
            raise serializers.ValidationError("A pending deletion request already exists for this user.")
        # check if the requestor is a list manager and the user to be deleted is in their player list
        requestor = self.context['request'].user
        if not hasattr(requestor, 'player_list_manager'):
            raise serializers.ValidationError("Only player list managers can request user deletions.")
        player_list = requestor.player_list_manager
        if player.player_list != player_list:
            raise serializers.ValidationError("The user to be deleted is not in your player list.")
        
        return super().validate(attrs)

    def create(self, validated_data):
        requestor = self.context['request'].user
        requested_at = datetime.datetime.now()
        deletion_request = DeletionRequest.objects.create(requested_by=requestor, requested_at=requested_at, player_to_be_deleted=validated_data.get('player_to_be_deleted'), status='PENDING')
        send_deletion_request_notification(deletion_request)
        return deletion_request
    
class ResetPasswordRequestSerializer(serializers.Serializer):
    token = serializers.CharField(write_only=True)
    mail = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        token = attrs.get('token')
        mail = attrs.get('mail')

        try:
            reset_requests = PasswordResetRequest.objects.filter(user__email=mail, used_at__isnull=True)
        except PasswordResetRequest.DoesNotExist:
            raise serializers.ValidationError("Invalid or used password reset token.")
        if not reset_requests.exists():
            raise serializers.ValidationError("Invalid or used password reset token.")
        for reset_request in reset_requests:
            if check_password(token, reset_request.token):
                if reset_request.expires_at > datetime.datetime.now(datetime.timezone.utc):
                    break
        else:
            raise serializers.ValidationError("Invalid or expired password reset token.")
        
        attrs['reset_request'] = reset_request
        return attrs
    
    def create(self, validated_data):
        new_password = validated_data.get('new_password')
        reset_request = validated_data.get('reset_request')

        user = reset_request.user
        user.set_password(new_password)
        user.save()
        reset_request.used_at = datetime.datetime.now(datetime.timezone.utc)
        reset_request.save()
        return reset_request
    
class CreatePasswordResetRequestSerializer(serializers.Serializer):
    mail = serializers.EmailField(write_only=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        mail = attrs.get('mail')
        try:
            user = User.objects.get(email=mail)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email.")
        attrs['user'] = user
        return attrs

    def create(self, validated_data):
        mail = validated_data.get('mail')
        user = User.objects.get(email=mail)
        reset_request, token = PasswordResetRequest.create_request(user=user)
        send_password_reset_email(reset_request, token)
        return reset_request
    
class ConfirmUserMailVerificationSerializer(serializers.Serializer):
    mail = serializers.EmailField(write_only=True)
    token = serializers.CharField(write_only=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        mail = attrs.get('mail')
        token = attrs.get('token')

        try:
            verifications = UserMailVerification.objects.filter(user__email=mail)
        except UserMailVerification.DoesNotExist:
            raise serializers.ValidationError("Invalid verification token.")
        
        if not verifications.exists():
            raise serializers.ValidationError("Invalid verification token.")

        for verification in verifications:
            if check_password(token, verification.token):
                break
        else:
            raise serializers.ValidationError("Invalid verification token.")

        attrs['verification'] = verification
        return attrs

    def create(self, validated_data):
        verification = validated_data.get('verification')
        verification.verified_at = datetime.datetime.now(datetime.timezone.utc)
        verification.save()
        player = verification.user.player_user
        player.email_verified = True
        player.save()

        return verification
    
class CreateUserMailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        email = attrs.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email.")
        attrs['user'] = user
        return attrs

    def create(self, validated_data):
        user = validated_data.get('user')
        verification, token = UserMailVerification.create_verification(user)
        send_email_verification_email(verification, token)
        return verification
    
class UploadedMedicalCertificateSerializer(serializers.Serializer):
    expires_at = serializers.DateField()
    file = serializers.FileField()
    confirmed_at = serializers.DateTimeField(required=False, allow_null=True)


    def validate(self, attrs):
        attrs =  super().validate(attrs)
        request = self.context.get('request')
        # check certificate has been uploaded by the player themselves
        player = Player.objects.get(user=request.user)
        if not player:
            raise serializers.ValidationError("No player found for this user.")
    
    def create(self, validated_data):
        request = self.context.get('request')
        player = Player.objects.get(user=request.user)
        medical_certificate = MedicalCertificate.objects.create(player=player, uploaded_at=datetime.datetime.now(datetime.timezone.utc), expires_at=validated_data.get('expires_at'), file=validated_data.get('file'), confirmed_at=validated_data.get('confirmed_at'))
        return medical_certificate
    
    def update(self, instance, validated_data):
        instance.expires_at = validated_data.get('expires_at', instance.expires_at)
        instance.file = validated_data.get('file', instance.file)
        instance.confirmed_at = validated_data.get('confirmed_at', instance.confirmed_at)
        instance.save()
        return instance
