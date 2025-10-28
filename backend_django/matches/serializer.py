from rest_framework import serializers
from .models import LocalLeague, Player, Stadium, Team

class ExtraFieldsSerializer(serializers.Serializer):

    def get_field_names(self, declared_fields, info):
        expanded_fields = super(ExtraFieldsSerializer, self).get_field_names(declared_fields, info)

        if getattr(self.Meta, 'extra_fields', None):
            return expanded_fields + self.Meta.extra_fields
        else:
            return expanded_fields
        
class LocalLeagueSerializer(ExtraFieldsSerializer, serializers.ModelSerializer):
    class Meta:
        model = LocalLeague
        fields = '__all__'
        extra_fields = ['teams', 'stadiums']
        depth = 1

class TeamSerializer(ExtraFieldsSerializer,serializers.ModelSerializer):
    local_league = serializers.SlugRelatedField(
        read_only=False,
        queryset=LocalLeague.objects.all(),
        slug_field='slug'
    )

    class Meta:
        model = Team
        fields = '__all__'
        extra_fields = ['players']   
        depth = 1     


class PlayerSerializer(serializers.ModelSerializer):
    team = serializers.SlugRelatedField(
        read_only=False,
        queryset=Team.objects.all(),
        slug_field='slug'
    )
    class Meta:
        model = Player
        fields = '__all__'


class StadiumSerializer(serializers.ModelSerializer):
    local_leagues = serializers.SlugRelatedField(
        read_only=False,
        many=True,
        queryset=LocalLeague.objects.all(),
        slug_field='slug'
    )
    class Meta:
        model = Stadium
        fields = '__all__'
        
