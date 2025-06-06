from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from simple_history.admin import SimpleHistoryAdmin
from django.contrib.auth.forms import AdminUserCreationForm

from .forms import CustomUserChangeForm
from .models import CustomUser, Device, AdministrationGroup, DeviceRoleProd, DNSDomain


class DeviceAdmin(SimpleHistoryAdmin):
    def get_readonly_fields(self, request, obj=None):  # overrides default get_readonly_fields-function
        # field only visible for staff and admins
        if request.user.is_superuser or request.user.is_staff:
            return ('modified_by', 'last_modified', 'creationDate',)
        return ()


class CustomUserAdmin(UserAdmin):
    add_form = AdminUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ["email", "username"]
    fieldsets = UserAdmin.fieldsets + ((None, {"fields": ("administration_group",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + ((None, {"fields": ("email", "administration_group",)}),)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Device, SimpleHistoryAdmin)
admin.site.register(AdministrationGroup)
admin.site.register(DeviceRoleProd)
admin.site.register(DNSDomain)
