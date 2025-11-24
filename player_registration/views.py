# from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated 
from .models import DeletionRequest, Player, PlayerList
from .serializer import CreatePasswordResetRequestSerializer, DeletionRequestSerializer, PlayerRegistrationForManagerSerializer, PlayerSerializer, PlayerListSerializer, PlayerRegistrationSerializer, ResetPasswordRequestSerializer
from rest_framework import mixins
from knox.views import LoginView as KnoxLoginView
from rest_framework.authentication import BasicAuthentication
from .permissions import AllowSelf, AllowIfManager



# Create your views here.
class PlayerViewSet(viewsets.ModelViewSet):
    # queryset = Player.objects.all()
    serializer_class = PlayerSerializer
    permission_classes = [IsAuthenticated & (AllowSelf | AllowIfManager)]

    def get_queryset(self):
        return Player.objects.filter(user = self.request.user) | Player.objects.filter(player_list__manager=self.request.user)

class PlayerListViewSet(viewsets.ModelViewSet):
    # queryset = PlayerList.objects.all()
    serializer_class = PlayerListSerializer
    permission_classes = [IsAuthenticated & AllowIfManager]

    def get_queryset(self):
        return PlayerList.objects.filter(manager=self.request.user)


class PlayerRegistrationViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    http_method_names = ['post']
    permission_classes = [AllowAny]
    serializer_class = PlayerRegistrationSerializer

class PlayerRegistrationForManagerViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    http_method_names = ['post']
    permission_classes = [IsAuthenticated]
    serializer_class = PlayerRegistrationForManagerSerializer

class LoginView(KnoxLoginView):
    authentication_classes = [BasicAuthentication]

class DeletionRequestViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post' ]
    serializer_class = DeletionRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DeletionRequest.objects.filter(requested_by=self.request.user)
    
class ResetPasswordRequestViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    http_method_names = ['post']
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordRequestSerializer

class CreatePasswordResetRequestViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    http_method_names = ['post']
    permission_classes = [AllowAny]
    serializer_class = CreatePasswordResetRequestSerializer

