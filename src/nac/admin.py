from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser, Device, Area, DeviceRoleProd, DeviceRoleInst


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ["email", "username"]
    fieldsets = UserAdmin.fieldsets + ((None, {"fields": ("area",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + ((None, {"fields": ("email", "area",)}),)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Device)
admin.site.register(Area)
admin.site.register(DeviceRoleProd)
admin.site.register(DeviceRoleInst)
