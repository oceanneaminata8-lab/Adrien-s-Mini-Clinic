from rest_framework.permissions import BasePermission, SAFE_METHODS


def user_role(user):
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        return 'admin'
    profile = getattr(user, 'clinic_profile', None)
    return profile.role if profile else None


class IsClinicStaff(BasePermission):
    def has_permission(self, request, view):
        return user_role(request.user) in {'admin', 'doctor', 'receptionist', 'lab', 'pharmacist'}


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return user_role(request.user) == 'admin'


class RoleBasedModelPermission(BasePermission):
    read_roles = {'admin', 'doctor', 'receptionist', 'lab', 'pharmacist'}
    write_roles = {'admin'}

    def has_permission(self, request, view):
        role = user_role(request.user)
        if request.method in SAFE_METHODS:
            return role in self.read_roles or role == 'patient'
        return role in self.write_roles


class ActionRolePermission(BasePermission):
    def has_permission(self, request, view):
        role = user_role(request.user)
        rules = getattr(view, 'role_permissions', {})
        allowed = rules.get(getattr(view, 'action', None), rules.get('default', {'admin'}))
        return role in allowed
