from dal import autocomplete
from ..models import DeviceRoleProd, AuthorizationGroup, DNSDomain
from django.contrib.auth.mixins import LoginRequiredMixin


class DNSDomainAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return DNSDomain.objects.none()

        qs = DNSDomain.objects.all().order_by('id')

#        autocomplete search results
        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs


class DeviceRoleProdAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return DeviceRoleProd.objects.none()

        qs = DeviceRoleProd.objects.all().order_by('id')

#        autocomplete search results
        if self.q:
            qs = qs.filter(name__istartswith=self.q)

#        only show DeviceRoleProd compatible with selected authorization_group
        authorization_group_pk = self.forwarded.get("authorization_group", None)

        if authorization_group_pk:
            authorization_group = AuthorizationGroup.objects.get(pk=authorization_group_pk)
            qs = qs.filter(id__in=authorization_group.DeviceRoleProd.all())

        return qs


class AuthorizationGroupAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return AuthorizationGroup.objects.none()

        qs = AuthorizationGroup.objects.all().order_by('id')

#        only show authorization_groups compatible with user
        qs = qs.filter(id__in=self.request.user.authorization_group.all())

#        autocomplete search results
        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs
