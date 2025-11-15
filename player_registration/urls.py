from django.urls import include, path
from rest_framework import routers
from knox import views as knox_views


# from .views import *
from .views import *


router = routers.DefaultRouter()
router.register(r'players', PlayerViewSet, basename='player')
router.register(r'player-lists', PlayerListViewSet, basename='player-list')
router.register(r'player-registration', PlayerRegistrationViewSet, basename='player-registration')

urlpatterns = [
    path('', include(router.urls)),
    # path('register-player/', PlayerRegistration.as_view(), name='player-registration'),
    path('login/', LoginView.as_view(), name='knox_login'),
    path(r'logout/', knox_views.LogoutView.as_view(), name='knox_logout'),
    path(r'logoutall/', knox_views.LogoutAllView.as_view(), name='knox_logoutall'),
]