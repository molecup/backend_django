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