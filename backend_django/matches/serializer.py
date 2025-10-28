from rest_framework import serializers
from .models import LocalLeague, Match, MatchEvent, Player, Stadium, Team, TeamParticipationMatch

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

class MatchEventSerializer(serializers.ModelSerializer):
    team_match = serializers.PrimaryKeyRelatedField(
        read_only=False,
        queryset=TeamParticipationMatch.objects.all()
    )
    player = serializers.PrimaryKeyRelatedField(
        read_only=False,
        queryset=Player.objects.all()
    )
    class Meta:
        model = MatchEvent
        fields = '__all__'

class TeamParticipationMatchSerializer(serializers.ModelSerializer):
    # team = serializers.SlugRelatedField(
    #     read_only=False,
    #     queryset=Team.objects.all(),
    #     slug_field='slug'
    # )
    team = TeamSerializer(read_only=True)
    events = MatchEventSerializer(many=True, read_only=True)
    class Meta:
        model = TeamParticipationMatch
        fields = ['id', 'is_home', 'penalties', 'score', 'team', 'events']

class MatchSerializer(serializers.ModelSerializer):
    # team_scores = serializers.SerializerMethodField()
    # def get_team_scores(self, obj):
    #     qset = TeamParticipationMatch.objects.filter(match=obj)
    #     return [TeamParticipationMatchSerializer(tp).data for tp in qset]

    teams = TeamParticipationMatchSerializer(many=True, source='participations', read_only=True)

    class Meta:
        model = Match
        fields = ['id', 'datetime', 'stadium', 'score_text', 'name', 'finished', 'teams']
        depth=1
