from django.contrib.auth.mixins import PermissionRequiredMixin

class CustomPermissionsRequiredMixin(PermissionRequiredMixin):
    def get_permission_denied_message(self):
        return "You do not have sufficient permissions to access this page."
