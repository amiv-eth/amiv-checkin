function confirm_close_event() {
    var r = confirm("Do you really want to close the event?\n" +
        "--> remaining participants will be checked out (applicable only for attendance tracking)\n" +
        "--> No more changes can be done on a closed event. If you want to open the event again, " +
        "assign a new PIN to the event via Credentials Login.\n" +
        "--> This might take some time, be patient.");
    if (r == true) {
        var url = "{{ url_for('checkin.close_event') }}";
        var form = $('<form action="' + url + '" method="POST">' +
            '{{ csrfcheckform.hidden_tag() }}' +
            '</form>');
        $('body').append(form);
        form.submit();
    }
}
