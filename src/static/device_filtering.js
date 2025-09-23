const search_form = $("#search_form")
const results_div = $('#results')
const endpoint = '/devices/'
const delay_by_in_ms = 700
let scheduled_function = false

let ajax_call = function (endpoint, request_parameters) {
    $.getJSON(endpoint, request_parameters)
        .done(response => {
                // replace the HTML contents
                results_div.html(response['html'])
            })
}

search_form.on('input', function () {

    const request_parameters = {
        search_string: $('#id_search_string').val(),
        device_role_prod: $('#id_device_role_prod').val(),
        administration_group: $('#id_administration_group').val(),
        show_deleted: $('#id_show_deleted').val(),
        appl_NAC_Active: $('#id_appl_NAC_Active').is(':checked') ? 'on' : undefined,
        appl_NAC_Install: $('#id_appl_NAC_Install').is(':checked') ? 'on' : undefined,
        appl_NAC_AllowAccessCAB: $('#id_appl_NAC_AllowAccessCAB').is(':checked') ? 'on' : undefined,
        appl_NAC_AllowAccessAIR: $('#id_appl_NAC_AllowAccessAIR').is(':checked') ? 'on' : undefined,
        appl_NAC_AllowAccessVPN: $('#id_appl_NAC_AllowAccessVPN').is(':checked') ? 'on' : undefined,
        appl_NAC_AllowAccessCEL: $('#id_appl_NAC_AllowAccessCEL').is(':checked') ? 'on' : undefined,
        allowLdapSync: $('#id_allowLdapSync').is(':checked') ? 'on' : undefined,
    }

    // if scheduled_function is NOT false, cancel the execution of the function
    if (scheduled_function) {
        clearTimeout(scheduled_function)
    }

    // setTimeout returns the ID of the function to be executed
    scheduled_function = setTimeout(ajax_call, delay_by_in_ms, endpoint, request_parameters);
})