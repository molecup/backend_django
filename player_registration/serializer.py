from rest_framework import serializers
from .models import Player, Parent, PlayerList
from django.contrib.auth.models import User

class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = "__all__"

class PlayerListSerializer(serializers.ModelSerializer):
    registration_token = serializers.ReadOnlyField()
    class Meta:
        model = PlayerList
        fields = ['id', 'name', 'manager', 'registration_token', 'team']
        
class PlayerListRestrictedSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerList
        fields = ['id', 'name']

class PlayerSerializer(serializers.ModelSerializer):
    parent = ParentSerializer(required=False, allow_null=True)
    player_list = PlayerListRestrictedSerializer(read_only=True)

    class Meta:
        model = Player
        fields = [
            'id', 'user', 'first_name', 'last_name', 'date_of_birth',
            'code_fiscal', 'shirt_number', 'shirt_size', 'position', 'parent', 'player_list'
        ]

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
            if instance.parent:
                for attr, value in parent_data.items():
                    setattr(instance.parent, attr, value)
                instance.parent.save()
            else:
                parent_instance = Parent.objects.create(**parent_data)
                instance.parent = parent_instance

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
        return attrs

    def create(self, validated_data):

        mail = validated_data.pop('mail')
        password = validated_data.pop('password')
        registration_token = validated_data.pop('player_list_token')

        user = User.objects.create_user(username=mail, email=mail, password=password)
        player_list = PlayerList.objects.get(registration_token=registration_token)

        player = Player.objects.create(user=user, player_list=player_list)
        return player
    
class PlayerShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ['id', 'first_name', 'last_name']

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