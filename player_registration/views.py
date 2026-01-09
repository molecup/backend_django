# from django.shortcuts import render
from io import BytesIO, StringIO
from time import timezone
import zipfile
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated 
from .models import DeletionRequest, MedicalCertificate, PaymentTransaction, Player, PlayerList
from .serializer import ChangePlayerMailSerializer, CheckOutPaymentSerializer, ConfirmUserMailVerificationSerializer, CreatePasswordResetRequestSerializer, CreateUserMailVerificationSerializer, DeletionRequestSerializer, MedicalCertificateSerializer, PlayerRegistrationForManagerSerializer, PlayerSerializer, PlayerListSerializer, PlayerRegistrationSerializer, ResetPasswordRequestSerializer
from rest_framework import mixins
from knox.views import LoginView as KnoxLoginView
from rest_framework.authentication import BasicAuthentication
from .permissions import AllowSelf, AllowIfManager, AllowEditIfNotSubmitted
import csv
from django.http import HttpResponse



# Create your views here.
class PlayerViewSet(viewsets.ModelViewSet):
    # queryset = Player.objects.all()
    serializer_class = PlayerSerializer
    permission_classes = [IsAuthenticated & (AllowSelf | AllowIfManager) & AllowEditIfNotSubmitted]

    def get_queryset(self):
        return Player.objects.filter(user = self.request.user) | Player.objects.filter(player_list__manager=self.request.user)

class PlayerListViewSet(viewsets.ModelViewSet):
    # queryset = PlayerList.objects.all()
    serializer_class = PlayerListSerializer
    permission_classes = [IsAuthenticated & AllowIfManager & AllowEditIfNotSubmitted]

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

class CreateUserMailVerificationViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    http_method_names = ['post']
    permission_classes = [AllowAny]
    serializer_class = CreateUserMailVerificationSerializer

class ConfirmUserMailVerificationViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    http_method_names = ['post']
    permission_classes = [AllowAny]
    serializer_class = ConfirmUserMailVerificationSerializer

#N.B. the pk is the player pk
class MedicalCertificateViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']
    permission_classes = [IsAuthenticated & (AllowSelf | AllowIfManager)]
    serializer_class = MedicalCertificateSerializer

    def get_queryset(self):
        return MedicalCertificate.objects.filter(player__user=self.request.user) | MedicalCertificate.objects.filter(player__player_list__manager=self.request.user)

# create an API endpoint to submit a playerList. Check if the user is the manager of the playerList. If so, set the submitted_at field to the current time.
@api_view(['POST'])
@permission_classes([IsAuthenticated & AllowIfManager])
def submit_player_list(request, pk):
    try:
        player_list = PlayerList.objects.get(pk=pk)
    except PlayerList.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if player_list.manager != request.user:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    num_sub_players = player_list.num_submitted_players()
    if num_sub_players < 22:
        return Response({"detail": "At least 22 players must be submitted to submit the player list."}, status=status.HTTP_400_BAD_REQUEST)

    if num_sub_players > 25: 
        return Response({"detail": "No more than 25 players can be submitted to submit the player list."}, status=status.HTTP_400_BAD_REQUEST)
    
    player_list.submitted_at = timezone.now()
    player_list.save()
    return Response(status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_player_list_csv(request, pk):
    try:
        player_list = PlayerList.objects.get(pk=pk)
    except PlayerList.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if not (player_list.manager == request.user or request.user.has_perm('player_registration.view_playerlist')):
        return Response(status=status.HTTP_403_FORBIDDEN)

    players = player_list.players.all()
    
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="player_list_{player_list.name}.csv"'},
    )

    writer = csv.writer(response)
    writer.writerow(['Status', 'Payment', 'First Name', 'Last Name', 'Email', 'cf', 'Date of Birth', 'Place of birth', 'Shirt size', 'Shirt number', 'Position']) 
    for player in players:
        writer.writerow([
            'Submitted' if player.registration_status == 'SUB' else 'Not Submitted',
            'Received' if player.payed else 'Missing',
            player.first_name,
            player.last_name,
            player.user.email,
            player.code_fiscal,
            player.date_of_birth.strftime('%Y-%m-%d') if player.date_of_birth else '',
            player.place_of_birth or '',
            player.shirt_size or '',
            player.shirt_number or '',
            player.position or ''
        ])
    
    return response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_bulk_player_list_csv(request):
    # Get list of player list IDs from query params
    pk_list = request.GET.get('pks', '')
    if not pk_list:
        return Response({"detail": "No player list IDs provided."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        pks = [int(pk.strip()) for pk in pk_list.split(',')]
    except ValueError:
        return Response({"detail": "Invalid player list IDs format."}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check permissions and filter player lists
    player_lists = PlayerList.objects.filter(pk__in=pks)
    
    if not request.user.has_perm('player_registration.view_playerlist'):
        return Response(status=status.HTTP_403_FORBIDDEN)
    
    if not player_lists.exists():
        return Response({"detail": "No player lists found."}, status=status.HTTP_404_NOT_FOUND)
    
    # Create a zip file containing all CSV files
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for player_list in player_lists:
            players = player_list.players.all()
            
            # Create CSV in memory
            csv_buffer = StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerow(['Status', 'Payment', 'First Name', 'Last Name', 'Email', 'cf', 'Date of Birth', 'Place of birth', 'Shirt size', 'Shirt number', 'Position'])
            
            for player in players:
                writer.writerow([
                    'Submitted' if player.registration_status == 'SUB' else 'Not Submitted',
                    'Received' if player.payed else 'Missing',
                    player.first_name,
                    player.last_name,
                    player.user.email,
                    player.code_fiscal,
                    player.date_of_birth.strftime('%Y-%m-%d') if player.date_of_birth else '',
                    player.place_of_birth or '',
                    player.shirt_size or '',
                    player.shirt_number or '',
                    player.position or ''
                ])
            
            # Add CSV to zip with sanitized filename
            safe_name = player_list.name.replace('/', '_').replace('\\', '_')
            zip_file.writestr(f"player_list_{safe_name}.csv", csv_buffer.getvalue())
    
    # Prepare response
    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer.read(), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="player_lists_export.zip"'
    
    return response

class PaymentTransactionViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    http_method_names = ['post']
    serializer_class = CheckOutPaymentSerializer 
    permission_classes = [AllowAny]

    def get_queryset(self):
        return PaymentTransaction.objects.filter(payer_email=self.request.user.email)
    
class ChangePlayerMailViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    http_method_names = ['post']
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePlayerMailSerializer