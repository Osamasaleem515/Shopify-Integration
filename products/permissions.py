from rest_framework import permissions


class IsInProductManagerGroup(permissions.BasePermission):
    """
    Custom permission to only allow members of the 'Product Managers' group to access the API.
    """
    message = "You must be a member of the 'Product Managers' group to perform this action."

    def has_permission(self, request, view):
        # Allow read operations for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Check if user is in the required group for write operations
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.groups.filter(name='Product Managers').exists()
        )


class IsAdminUserOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admin users to edit products.
    Regular authenticated users can view but not edit.
    """
    def has_permission(self, request, view):
        # Allow read operations for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
            
        # Write permissions are only allowed to admin users
        return request.user and request.user.is_staff 