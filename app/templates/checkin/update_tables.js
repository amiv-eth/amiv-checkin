
function beautify_legi(rawlegi) {
    if (rawlegi == null) {
        legi = "unknown";
    } else {
        legi = rawlegi;
    }
    return legi;
}

function beautify_checkin(rawchecked_in) {
    if (rawchecked_in == null) {
        checked_in = "-";
    } else if(rawchecked_in == true) {
        checked_in = "IN";
    } else {
        checked_in = "OUT";
    }
    return checked_in;
}

$(document).ready(function() {
    setInterval(function() {
    $.ajax({
        type: 'get',
        url: '{{ url_for('checkin.checkin_update_data') }}',
        dataType: 'json',
        success: function(data) {
            $('#sync_warning').hide();

            var newRows = "";
            for (var i in data.signups) {
                newRows += "<tr><td>" + data.signups[i].firstname + " " + data.signups[i].lastname + "</td>"
                newRows += "<td>" + data.signups[i].nethz + "</td>"
                newRows += "<td>" + beautify_legi(data.signups[i].legi) + "</td>"
                newRows += "<td>" + data.signups[i].email + "</td>"
                newRows += "<td>" + beautify_checkin(data.signups[i].checked_in) + "</td></tr>";
            }
            $('#tbody_signups').html(newRows);

            var newStats = "";
            for (var i in data.statistics) {
                newStats += "<tr><td width='85%'>" + data.statistics[i].key + "</td>"
                newStats += "<td width='15%'>" + data.statistics[i].value + "</td></tr>";
            }
            $("#tbody_statistics").html(newStats);
        },
        error: function() {
            $('#sync_warning').show();
        }
    });
    }, 5000);
});

