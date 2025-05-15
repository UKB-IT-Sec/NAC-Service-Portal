from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser, Device, AuthorizationGroup, DeviceRoleProd, DeviceRoleInst, DNSDomain


class DeviceAdmin(admin.ModelAdmin):

    def get_readonly_fields(self, request, obj=None):  # overrides default get_readonly_fields-function
        # modified_by only visible for staff and admins
        if request.user.is_superuser or request.user.is_staff:
            return ('modified_by',)
        return ()


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ["email", "username"]
    fieldsets = UserAdmin.fieldsets + ((None, {"fields": ("authorization_group",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + ((None, {"fields": ("email", "authorization_group",)}),)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Device, DeviceAdmin)
admin.site.register(AuthorizationGroup)
admin.site.register(DeviceRoleProd)
admin.site.register(DeviceRoleInst)
admin.site.register(DNSDomain)
