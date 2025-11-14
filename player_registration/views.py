# from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import Player, PlayerList
from .serializer import PlayerSerializer, PlayerListSerializer, PlayerRegistrationSerializer
from rest_framework import mixins
from knox.views import LoginView as KnoxLoginView
from rest_framework.authentication import BasicAuthentication



# Create your views here.
class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

class PlayerListViewSet(viewsets.ModelViewSet):
    queryset = PlayerList.objects.all()
    serializer_class = PlayerListSerializer

# # add view for Player registration 
# @api_view(['POST'])
# @permission_classes([AllowAny])
# def register_player(request):
#     serializer = PlayerRegistrationSerializer(data=request.data)
#     if serializer.is_valid():
#         player = serializer.save()
#         return Response({'status': 'Player registered successfully'}, status=status.HTTP_201_CREATED)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PlayerRegistrationViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    http_method_names = ['post']
    permission_classes = [AllowAny]
    serializer_class = PlayerRegistrationSerializer

class LoginView(KnoxLoginView):
    authentication_classes = [BasicAuthentication]

