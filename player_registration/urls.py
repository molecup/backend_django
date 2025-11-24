from django.urls import include, path
from rest_framework import routers
from knox import views as knox_views


# from .views import *
from .views import *


router = routers.DefaultRouter()
router.register(r'players', PlayerViewSet, basename='player')
router.register(r'player-lists', PlayerListViewSet, basename='player-list')
router.register(r'player-registration', PlayerRegistrationViewSet, basename='player-registration')
router.register(r'player-registration-for-manager', PlayerRegistrationForManagerViewSet, basename='player-registration-for-manager')
router.register(r'deletion-requests', DeletionRequestViewSet, basename='deletion-request')
router.register(r'reset-password-requests', ResetPasswordRequestViewSet, basename='reset-password-request')
router.register(r'create-password-reset-request', CreatePasswordResetRequestViewSet, basename='create-password-reset-request')
router.register(r'create-user-mail-verification', CreateUserMailVerificationViewSet, basename='create-user-mail-verification')
router.register(r'confirm-user-mail-verification', ConfirmUserMailVerificationViewSet, basename='confirm-user-mail-verification')

urlpatterns = [
    path('', include(router.urls)),
    # path('register-player/', PlayerRegistration.as_view(), name='player-registration'),
    path('login/', LoginView.as_view(), name='knox_login'),
    path(r'logout/', knox_views.LogoutView.as_view(), name='knox_logout'),
    path(r'logoutall/', knox_views.LogoutAllView.as_view(), name='knox_logoutall'),
]