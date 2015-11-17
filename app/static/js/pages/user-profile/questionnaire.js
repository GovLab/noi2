$(function() {
  if (window.location.hash == '') {
    // We're likely on Safari, which doesn't like to keep URL fragments
    // on redirect: https://bugs.webkit.org/show_bug.cgi?id=24175
    //
    // Because this is the questionnaire, we *really* need the page
    // to be focused on the current question on page load, so we'll
    // forcibly scroll down to it ourselves.
    $('#expertise')[0].scrollIntoView();
  }
});
