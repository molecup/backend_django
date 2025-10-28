# from django.shortcuts import render
from html import entities
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, viewsets
from .models import LocalLeague, Stadium, Team, Player
from .serializer import LocalLeagueSerializer, StadiumSerializer, TeamSerializer, PlayerSerializer

# # Factories.
# def handlers_factory(Model, Serializer):
#     """
#     Factory function to create a view for managing (GET, PUT, DELETE) a single entity.
#     Args:
#         Model: The Django model class.
#         Serializer: The corresponding serializer class.
#     """
#     @api_view(['GET', 'PUT', 'DELETE'])
#     def entity_manager(*args, **kvargs):
#         request = args[0]
#         try:
#             league = Model.objects.get(**kvargs)
#         except Model.DoesNotExist:
#             return Response(status=status.HTTP_404_NOT_FOUND)

#         #get entity
#         if request.method == 'GET':
#             serializer = Serializer(league)
#             return Response(serializer.data)

#         #update entity
#         if request.method == 'PUT':
#             serializer = LocalLeagueSerializer(league, data=request.data, partial=True)
#             if serializer.is_valid():
#                 serializer.save()
#                 return Response(serializer.data)
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         #delete entity
#         if request.method == 'DELETE':
#             league.delete()
#             return Response(status=status.HTTP_204_NO_CONTENT)
        
#     @api_view(['GET', 'POST'])
#     def collection_manager(request):
#         queryset = Model.objects.all()
#         #get all entities
#         if request.method == 'GET':
#             queryset = Model.objects.all()
#             serializer = Serializer(queryset, many=True)
#             return Response(serializer.data)

#         #create new entity
#         if request.method == 'POST':
#             serializer = Serializer(data=request.data)
#             if serializer.is_valid():
#                 serializer.save()
#                 return Response(serializer.data, status=status.HTTP_201_CREATED)
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
#     return {
#         'entity_manager': entity_manager,
#         'collection_manager': collection_manager
#     }



# # Views instantiations using factories

# team_handlers = handlers_factory(Team, TeamSerializer)
# local_league_handlers = handlers_factory(LocalLeague, LocalLeagueSerializer)
# player_handlers = handlers_factory(Player, PlayerSerializer)

class LocalLeagueViewSet(viewsets.ModelViewSet):
    queryset = LocalLeague.objects.all()
    serializer_class = LocalLeagueSerializer
    lookup_field = 'slug'

class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    lookup_field = 'slug'

class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

class StadiumViewSet(viewsets.ModelViewSet):
    queryset = Stadium.objects.all()
    serializer_class = StadiumSerializer


