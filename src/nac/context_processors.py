from helper.armis import get_tenant_url


# is armis configured? We need this to render to nav-bar correctly
def armis_context(request):
    # if no tenant url is given in the config, get_tenant_url() returns "https://"
    armis_is_configured = get_tenant_url() != "https://"
    print(get_tenant_url())
    return {"armis_is_configured": armis_is_configured}
