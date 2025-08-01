from dal import autocomplete
from ..models import DeviceRoleProd, AdministrationGroup, DNSDomain
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin


class DNSDomainAutocomplete(LoginRequiredMixin, PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    permission_required = "nac.view_device"

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return DNSDomain.objects.none()

        qs = DNSDomain.objects.all().order_by('id')

#        autocomplete search results
        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs


class DeviceRoleProdAutocomplete(LoginRequiredMixin, PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    permission_required = "nac.view_device"

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return DeviceRoleProd.objects.none()

        qs = DeviceRoleProd.objects.all().order_by('id')

#        autocomplete search results
        if self.q:
            qs = qs.filter(name__istartswith=self.q)

#        only show DeviceRoleProd compatible with selected administration_group
        administration_group_pk = self.forwarded.get("administration_group", None)

        if administration_group_pk:
            administration_group = AdministrationGroup.objects.get(pk=administration_group_pk)
            qs = qs.filter(id__in=administration_group.DeviceRoleProd.all())

        return qs


class AdministrationGroupAutocomplete(LoginRequiredMixin, PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    permission_required = "nac.view_device"

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return AdministrationGroup.objects.none()

        qs = AdministrationGroup.objects.all().order_by('id')

#        only show administration_groups compatible with user
        qs = qs.filter(id__in=self.request.user.administration_group.all())

#        autocomplete search results
        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs
