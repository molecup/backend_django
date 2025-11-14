from django.urls import include, path
from rest_framework import routers

# from .views import *
from .views import *


router = routers.DefaultRouter()
router.register(r'players', PlayerViewSet)
router.register(r'playerlists', PlayerListViewSet)

urlpatterns = [
    path('', include(router.urls)),
]