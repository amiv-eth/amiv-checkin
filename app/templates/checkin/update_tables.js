
function hide_flash_messages() {
    $('.alert').not('#sync_warning_alert').hide();
}

function beautify_legi(rawlegi) {
    if (rawlegi === null) {
        legi = "unknown";
    } else {
        legi = rawlegi;
    }
    return legi;
}

function beautify_checkin(rawchecked_in) {
    if (rawchecked_in === null) {
        checked_in = "-";
    } else if(rawchecked_in === true) {
        checked_in = "IN";
    } else {
        checked_in = "OUT";
    }
    return checked_in;
}

function beautify_membership(rawmembership) {
    return rawmembership.charAt(0).toUpperCase() + rawmembership.slice(1);
}

function update_data() {
    $.ajax({
        type: 'get',
        url: "{{ url_for('checkin.checkin_update_data') }}",
        dataType: 'json',
        success: function(data) {
            $('#sync_warning').hide();

            var newRows = "";
            for (var i in data.signups) {
                newRows += "<tr><td>" + data.signups[i].firstname + " " + data.signups[i].lastname + "</td>"
                newRows += "<td>" + data.signups[i].nethz + "</td>"
                newRows += "<td>" + beautify_legi(data.signups[i].legi) + "</td>"
                newRows += "<td>" + data.signups[i].email + "</td>"
                newRows += "<td>" + beautify_membership(data.signups[i].membership) + "</td>"
                if (data.signups[i].hasOwnProperty('checked_in')) {
                    newRows += "<td>" + beautify_checkin(data.signups[i].checked_in) + "</td></tr>";
                } else if (data.signups[i].hasOwnProperty('freebies_taken')) {
                    newRows += "<td>" + data.signups[i].freebies_taken + "</td></tr>";
                }
            }
            $('#tbody_signups').html(newRows);

            var newStats = "";
            for (var i in data.statistics) {
                newStats += "<tr><td width='85%'>" + data.statistics[i].key + "</td>"
                newStats += "<td width='15%'>" + data.statistics[i].value + "</td></tr>";
            }
            $("#tbody_statistics").html(newStats);
        },
        error: function(xhr, textStatus, thrownError) {
            var err = "(Error: ";
            err += textStatus;
            err += " HTTP ";
            err += xhr.status;
            err += ": ";
            err += xhr.responseText;
            err += ")";
            $("#sync_warning_reason").html(err);
            $('#sync_warning').show();

        }
    });
    }

$(document).ready(function() {
    update_data();
    setInterval(update_data, 5000);
    setTimeout(hide_flash_messages, 10000);
});
