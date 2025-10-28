from django.urls import include, path
from rest_framework import routers

# from .views import *
from .views import *

router = routers.DefaultRouter()
router.register(r'local-leagues', LocalLeagueViewSet)
router.register(r'teams', TeamViewSet)
router.register(r'players', PlayerViewSet)
router.register(r'stadiums', StadiumViewSet)

urlpatterns = router.urls