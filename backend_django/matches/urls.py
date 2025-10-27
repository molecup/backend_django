from django.urls import include, path
# from .views import *
from .views import *

ENDPOINTS_SLUG = [
    ('local-league/', local_league_handlers),
    ('team/', team_handlers),
]

ENDPOINTS_PK = [
    ('player/', player_handlers),
]

urlpatterns = [path(
    endpoint,
    include([
        path('<slug:slug>/', handlers['entity_manager'], name=f'{endpoint}-manager'),
        path('', handlers['collection_manager'], name=f'{endpoint}-collection'),
    ])
) for endpoint, handlers in ENDPOINTS_SLUG] + [path(
    endpoint,
    include([
        path('<int:pk>/', handlers['entity_manager'], name=f'{endpoint}-manager'),
        path('', handlers['collection_manager'], name=f'{endpoint}-collection'),
    ])
) for endpoint, handlers in ENDPOINTS_PK]