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
    var connectTo = $(evt.target).data('connect-to');
    if (connectTo) {
      $.post('/email', {
        'emails': connectTo.split(',')
      });
    }
  });

  // Advance tutorial steps
  $("[data-tutorial-step]").click(function (evt) {
    var step = $(evt.target).data('tutorial-step');
    if (step) {
      $.post('/tutorial', {
        'step': step
      });
    }
  });
});
