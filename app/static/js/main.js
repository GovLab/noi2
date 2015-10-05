/*jslint browser:true*/
/*globals $*/
var csrftoken = $('meta[name=csrf-token]').attr('content');

$.ajaxSetup({
  beforeSend: function(xhr, settings) {
    if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) &&
        !this.crossDomain) {
      xhr.setRequestHeader("X-CSRFToken", csrftoken);
    }
  }
});

$(document).ready(function () {
  // Keep track of mailto: links as connections
  $("a[href^=mailto]").click(function (evt) {
    var href = $(evt.target).attr('href'),
        emails = href.split(':')[1].split('?')[0].split(',');

    $.post('/email', {
      'emails': emails
    });
  });
});
