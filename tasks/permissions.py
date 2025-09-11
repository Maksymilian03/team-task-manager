from rest_framework import permissions

class IsTeamManagerOrAssigned(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.is_superuser:
            return True

        if not hasattr(user, 'profile'):
            return False

        profile = user.profile

        if profile.role == 'manager' and obj.team == profile.team:
            return True
        
        return obj.assigned_to == user