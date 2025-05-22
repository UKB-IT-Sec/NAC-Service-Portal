from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from simple_history.admin import SimpleHistoryAdmin
from django.contrib.auth.forms import AdminUserCreationForm

from .forms import CustomUserChangeForm
from .models import CustomUser, Device, AdministrationGroup, DeviceRoleProd, DeviceRoleInst, DNSDomain


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
admin.site.register(DeviceRoleInst)
admin.site.register(DNSDomain)
