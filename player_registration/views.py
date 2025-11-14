# from django.shortcuts import render
from rest_framework import status, viewsets
from .models import Player, PlayerList
from .serializer import PlayerSerializer, PlayerListSerializer


# Create your views here.
class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

class PlayerListViewSet(viewsets.ModelViewSet):
    queryset = PlayerList.objects.all()
    serializer_class = PlayerListSerializer