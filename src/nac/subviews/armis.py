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

from helper.armis import get_armis_sites, get_devices


class ArmisView(View):
    template_name = "armis_import.html"

    def _get_context(self):  # sets the site-context for armis_import.html, uses cache to be less time consuming
        context = {}
        armis_sites = cache.get('armis_sites')
        if armis_sites is None:
            armis_sites = get_armis_sites()
            cache.set('armis_sites', armis_sites, 3600)
        context['armis_sites'] = armis_sites
        return context

    def get(self, request, *args, **kwargs):  # rendering the html base with site-context
        context = self._get_context()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):  # gets site-id chosen in html-dropdown, gets Devices based on site-id, shows them via device-context
        context = self._get_context()

        selected_site = request.POST.get('site-id')
        context['selected_site'] = selected_site if selected_site else ''
        if selected_site:
            context['devices'] = get_devices(context['armis_sites'][selected_site])

        return render(request, self.template_name, context)
