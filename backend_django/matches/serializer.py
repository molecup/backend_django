from rest_framework import serializers
from .models import LocalLeague, Team, Player

class LocalLeagueSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocalLeague
        fields = '__all__'

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = '__all__'

class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = '__all__'
