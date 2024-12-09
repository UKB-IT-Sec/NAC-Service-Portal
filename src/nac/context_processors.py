from helper.armis import get_tenant_url
from django.core.cache import cache


# is armis configured? We need this to render to nav-bar correctly
def armis_context(request):
    armis_is_configured = cache.get("armis_is_configured")
    if armis_is_configured is None:
        armis_is_configured = get_tenant_url() != "https://"
        cache.set("armis_is_configured", armis_is_configured)
    return {"armis_is_configured": armis_is_configured}
