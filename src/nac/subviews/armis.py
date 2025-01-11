'''
    NSSP
    Copyright (C) 2024 Universitaetsklinikum Bonn AoeR

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
from django.views.generic import View
from django.core.cache import cache
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin


from helper.armis import get_armis_sites, get_devices, get_tenant_url, get_boundaries, map_ids_to_names, get_vlan_blacklist


class ArmisView(LoginRequiredMixin, View):
    template_name = "armis_import.html"

    def _get_context(self):  # sets the site-context for armis_import.html, uses cache to be less time consuming
        context = {}
        armis_sites = cache.get('armis_sites')
        if armis_sites is None:
            armis_sites = get_armis_sites()
            cache.set('armis_sites', armis_sites, 3600)
        context['armis_sites'] = armis_sites
        context['tenant_url'] = get_tenant_url()
        context['vlan_blacklist'] = get_vlan_blacklist()
        return context

    def get(self, request, *args, **kwargs):  # rendering the html base with site-context
        context = self._get_context()
        context['display'] = True
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):  # gets site-id chosen in html-dropdown, gets Devices based on site-id, shows them via device-context
        context = self._get_context()
        selected_sites = request.POST.getlist('site-ids[]')
        context['display'] = False if selected_sites else True
        context['selected_sites'] = selected_sites if selected_sites else ''
        if selected_sites:
            context['devices'] = get_devices(map_ids_to_names(selected_sites, context['armis_sites']))
            context['boundaries'] = get_boundaries(context['devices'])

        return render(request, self.template_name, context)
