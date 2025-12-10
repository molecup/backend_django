from rest_framework import permissions

class AllowSelf(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user'):
            return obj.user == request.user 
        return False
    
class AllowIfManager(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'manager'):
            return obj.manager == request.user 
        if hasattr(obj, 'player_list'):
            return obj.player_list.manager == request.user
        return False
    

class AllowEditIfNotSubmitted(permissions.BasePermission):
    """
    Custom permission to only allow edits if the player list has not been submitted. (GET requests are always allowed)
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if hasattr(obj, 'submitted_at'):
            return obj.submitted_at is None
        if hasattr(obj, 'player_list'):
            return obj.player_list.submitted_at is None
        return False