
function confirm_new_pin() {
  var r = confirm("Do you really want to re-generate the PIN?");
  if (r == true) {
    var url = "{{ url_for('checkin.change_pin') }}";
    var form = $('<form action="' + url + '" method="POST">' +
      '{{ changepinform.hidden_tag() }}' +
      '</form>');
    $('body').append(form);
    form.submit();
  }
}
