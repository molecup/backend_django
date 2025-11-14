from rest_framework import serializers
from .models import Player, Parent, PlayerList

class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = "__all__"

class PlayerListSerializer(serializers.ModelSerializer):
    registration_token = serializers.ReadOnlyField()
    class Meta:
        model = PlayerList
        fields = ['id', 'name', 'manager', 'registration_token', 'team']
        

class PlayerSerializer(serializers.ModelSerializer):
    parent = ParentSerializer(required=False, allow_null=True)

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
