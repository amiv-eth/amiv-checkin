function confirm_new_pin() {
  var r = confirm("Do you really want to re-generate the PIN?");
  if (r == true) {
      window.location.replace("{{ url_for('checkin.change_pin') }}");
  }
}
