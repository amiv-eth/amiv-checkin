
function confirm_close_event() {
  var r = confirm("Do you really want to check-out all remaining participants and close the event?\n" +
      "(No more check-ins can be done for a closed event. If you want to open the event again, " +
      "assign a new PIN to the event via Credentials Login.)\n" +
      "(This might take some time, be patient...)");
  if (r == true) {
    var url = "{{ url_for('checkin.close_event') }}";
    var form = $('<form action="' + url + '" method="POST">' +
      '{{ csrfcheckform.hidden_tag() }}' +
      '</form>');
    $('body').append(form);
    form.submit();
  }
}
