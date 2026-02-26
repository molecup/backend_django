from django.urls import include, path
from rest_framework import routers

# from .views import *
from .views import *
from .custom_admin_views import match_list_view, match_edit_view

router = routers.DefaultRouter()
router.register(r'local-leagues', LocalLeagueViewSet)
router.register(r'teams', TeamViewSet)
router.register(r'players', PlayerViewSet)
router.register(r'stadiums', StadiumViewSet)
router.register(r'matches', MatchViewSet)
router.register(r'match-events', MatchEventViewSet)
router.register(r'news', NewsViewSet)

urlpatterns = [
    path('management/matches/', match_list_view, name='custom_match_list'),
    path('management/matches/<int:match_id>/', match_edit_view, name='custom_match_edit'),
] + router.urls