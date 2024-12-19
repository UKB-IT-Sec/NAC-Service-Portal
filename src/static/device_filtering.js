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
        authorization_group: $('#id_authorization_group').val()
    }

    // if scheduled_function is NOT false, cancel the execution of the function
    if (scheduled_function) {
        clearTimeout(scheduled_function)
    }

    // setTimeout returns the ID of the function to be executed
    scheduled_function = setTimeout(ajax_call, delay_by_in_ms, endpoint, request_parameters);
})